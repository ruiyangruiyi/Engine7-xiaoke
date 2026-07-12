# Carpo bypass pull → fastrtc 集成方案

> 2026-07-09 小柯整理（父让我回顾往下接的方案）
> bypass 已通（62a2d5b1b），拉流端收到 raw Opus 字节

## 当前状态

```
268 (4090)                     本机 (Win11)
┌─────────────────┐           ┌──────────────────────────────┐
│ TTS → Opus →    │──UDP──▶  │ Carpo.dll pull               │
│ Carpo push      │  23800   │ bypass → callback_opus.raw ✓ │
└─────────────────┘           └──────────────────────────────┘
```

**下一步**：callback 收到 Opus → PyAV 解码 → fastrtc audio emit → 浏览器听到声音

---

## 架构

```
                    ┌───────── 本机 ───────────────────────────┐
                    │                                          │
268 push ──UDP──▶  │  Carpo pull (bypass)                      │
                    │    callback: raw Opus bytes               │
                    │      │                                    │
                    │      ▼ PyAV opus decode (mono, 48kHz)    │
                    │      │ PCM float32 chunks                 │
                    │      ▼ asyncio.Queue                      │
                    │      │                                    │
                    │  fastrtc AsyncAudioVideoStreamHandler      │
                    │    emit() → WebRTC audio track             │
                    │      │                                    │
                    │      ▼ 浏览器 <audio> 出声                │
                    └──────────────────────────────────────────┘
```

## 分阶段实施

### Phase 1: 纯音频（今天）

**目标**：pull → Opus decode → fastrtc → 浏览器能听到

**文件**：新建 `carpo_bypass_server.py`，复用 carpo_rtc_server.py 的 fastrtc 骨架，换 pipeline：
- pull 端用 bypass 模式（从 pull_play_auto.py 抄配置）
- media callback 内部 PyAV decode Opus → PCM float32
- PCM 入 asyncio queue → fastrtc emit()

**关键参数**：
| 参数 | 值 | 来源 |
|------|-----|------|
| audio SSRC local | 99999 | pull_play_auto.py |
| audio SSRC remote | 12345 | pull_play_auto.py |
| Opus sample rate | 48000 | push 端固定 |
| Opus channels | 1 (mono) | push 端改过 |
| fastrtc output SR | 48000 | 不用重采样 |
| fastrtc output frame | 960 samples (20ms) | Opus 帧大小 |

**PyAV Opus 解码**（已验证可用，pull_play_auto.py 之前用过）：
```python
import av
codec = av.CodecContext.create('opus', 'r')
# 每次回调收到 opus bytes 时：
packet = av.Packet(raw_opus)
frame = codec.decode(packet)[0]
pcm = frame.to_ndarray()  # shape (1, 960) float, mono 48kHz
pcm_mono = pcm.flatten()
```

### Phase 2: 接入 voice-chat 上行（2h）

**目标**：carpo_bypass_server 和 server.py（VAD→ASR→Engine→TTS）打通

两条路径同时跑：
1. **下行（听）**：Carpo pull → Opus decode → fastrtc emit → 浏览器出声
2. **上行（说）**：浏览器麦克风 → fastrtc receive → VAD → ASR → Engine → TTS → 268 push → 回到本机 pull

**上行触发**：浏览器的 fastrtc receive() 走现有 VAD 管线，Engine 回复文字调 TTS → 推 268 → pull 回来

### Phase 3: 加视频（4h）

**目标**：Carpo video SSRC (67890) 也拉，接 fastrtc video_emit

需要：
- pull 端 media callback 区分 audio/video（type 参数）
- video: H.264 NAL → PyAV decode → BGR → emit
- audio: Opus → PyAV decode → PCM → emit

268 已在推双流（audio SSRC 12345 + video SSRC 67890），pull 端只需加 video callback

---

## 对比现有代码

| 文件 | 状态 | 问题 |
|------|------|------|
| `carpo_rtc_server.py` | NetEq 模式，audio-only | NetEq 有尖峰音 |
| `carpo_pull_handler.py` | 试图按 NAL 起头分 audio/video | ❌ carpo 回调里不该这么分（media_type 已经区分） |
| `carpo_pull_server.py` | 用 `carpo_pull_handler` 的 fastrtc wrapper | 底层 handler 有问题 |
| **新 `carpo_bypass_server.py`** | **目标** | bypass + PyAV decode + fastrtc |

**策略**：不修旧文件，建新的。等新文件验证完后，旧文件可废弃或合并。

---

## 新文件 `carpo_bypass_server.py` 骨架

```python
"""phase1: bypass pull → Opus decode → fastrtc audio"""
import asyncio, ctypes, numpy as np
from fastrtc import Stream, AsyncAudioVideoStreamHandler
from fastapi import FastAPI
import uvicorn
import av

# --- carpo pull setup (同 pull_play_auto.py) ---
dll_path = ...
lib = carpo.load_lib(dll_path)

audio_queue = asyncio.Queue(maxsize=200)
opus_codec = av.CodecContext.create('opus', 'r')

def on_media(media_type, data_ptr, length, timestamp, user_data):
    if media_type == carpo.MEDIA_AUDIO:
        raw = bytes(ctypes.string_at(data_ptr, length))
        pkt = av.Packet(raw)
        try:
            frame = opus_codec.decode(pkt)
            if frame:
                pcm = frame[0].to_ndarray().flatten()  # float mono
                asyncio.run_coroutine_threadsafe(audio_queue.put(pcm), main_loop)
        except: pass

# --- fastrtc handler ---
class Handler(AsyncAudioVideoStreamHandler):
    async def emit(self):
        try:
            pcm = await asyncio.wait_for(audio_queue.get(), timeout=0.1)
            return (48000, pcm.astype(np.float32))
        except asyncio.TimeoutError:
            return (48000, np.zeros(960, dtype=np.float32))
```

---

## 待确认的问题

1. **Opus 帧可能不是整 960 samples** — bypass 回调收到的 opus 包可能是单个 RTP 包，PyAV decode 返回的 frame 长度可能不是精确 960。需要处理累积/补齐。

2. **pyaudio vs fastrtc** — pull_play_auto.py 之前用 pyaudio 播，改成 fastrtc 后可以扔掉 pyaudio 依赖。

3. **carpo.py CarpoPuller 的 callback 是 ctypes 线程** — `on_media` 在 C 线程调用，`asyncio.run_coroutine_threadsafe` 必须用主 event loop（`main_loop` 变量）。

4. **carpo_rtc_server.py 里的 `CarpoPuller` 用 `carpo.load_lib()` 不加参数** — 需要确认 DLL 搜索路径，pull_play_auto.py 用的 `dll_path` 是指定绝对路径的。

5. **carpo.py CarpoPuller 构造** — `CarpoPuller(lib, on_media, on_event)` 传 lib 和 callbacks

6. **是否需要 restart 机制** — carpo_rtc_server.py 有 restart_pull() 和 /push endpoint 触发重拉。Phase 1 先不搞，等跑通再优化。
