# 2026-07-20 aiortc 全 Passthrough 调研 + 踩坑

## 背景

fastrtc 的 `ServerToClientAudio` 有 1 分钟缓存延迟，且不支持视频。
翀哥要求用 aiortc 替代 fastrtc，实现 audio + video 实时传输。

## 核心认知（最宝贵）

### 1. aiortc 的 pack() 机制
aiortc 对 H.264 的处理链：
```
av.Packet (Annex B 格式)
  → H264Encoder.pack()
  → _split_bitstream() 按 00 00 00 01 start code 拆 NAL
  → _packetize() 按 RTP 规则分包（STAP-A 合并小 NAL，FU-A 拆大 NAL）
  → RTP packets 发到浏览器
```
**关键**：pack() 已经做了 RTP 分包，不需要自己处理。

### 2. 什么是 Passthrough
- **audio passthrough**：Opus raw bytes 直接塞进 av.Packet，不 decode 不 re-encode
- **video passthrough**：H.264 NAL raw bytes 直接塞进 av.Packet，不 decode 不 re-encode
- **零编解码延迟**——这是最低延迟的方案

### 3. Carpo SDK timestamp 机制（翀哥点醒）
- SDK pull 端的 timestamp 已经做了 base 对齐
- 第一个 audio 或 video 包 timestamp=0（谁先到谁 0）
- 后续都是相对 0 的差值（ms）
- **两个 track 共享同一个时间基准**——天然同步

### 4. PTS_MODE 开关设计
- `fixed`（默认）：固定累加（audio +960/帧 @48kHz, video +3600/帧 @90kHz），匀速稳定
- `sdk`：用 SDK timestamp × 时钟基准（audio ×48, video ×90）
- 实测：fixed 模式体验最好（不依赖 wall clock 抖动）

## 踩坑记录（4 个关键坑）

### 坑 1：callback 参数顺序
**现象**：Carpo callback 拿到的数据乱码/全零
**原因**：carpo callback 签名是 `(media_type, data_ptr, length, timestamp, user_data)`，不是 `(data_ptr, ..., media_type)`
**解法**：看官方 webcam 例子确认参数顺序
**教训**：不确定 API 签名时，直接看官方 example，不要猜

### 坑 2：跨线程 asyncio.Queue
**现象**：queue.put() 报 "no running event loop" 或卡住
**原因**：Carpo callback 在 C 线程，asyncio.Queue 在 event loop 线程，直接 put 不安全
**解法**：`loop.call_soon_threadsafe(queue.put_nowait, item)`
**教训**：C 线程调 Python 对象必须用 call_soon_threadsafe

### 坑 3：H.264 SPS/PPS 分包 → 浏览器无画面
**现象**：video track recv() 在调，pts 正常，但浏览器黑屏
**原因**：Carpo SDK 把 SPS（29 bytes）和 PPS（8 bytes）分成两个包发，aiortc pack() 各自独立打包，浏览器收到分散的 NAL 无法初始化 decoder
**解法**：在 callback 里攒包——SPS(7)/PPS(8) 暂存 buffer，等 IDR(5)/P-frame(1) 来了拼接成一个 Annex B 包发出
**教训**：浏览器 H.264 decoder 需要 SPS+PPS+IDR 在同一个 access unit

### 坑 4：setCodecPreferences 顺序
**现象**：强制 H264 没生效，answer SDP 的 m=video 第一个还是 VP8
**原因**：setCodecPreferences 放在 setRemoteDescription 之后，aiortc 在 setRemoteDescription 时已经用 default codec 列表做了过滤
**解法**：setCodecPreferences 必须在 **addTrack 之后、setRemoteDescription 之前**调用
**教训**：aiortc 的 transceiver codec 协商在 setRemoteDescription 时发生，preferences 必须提前设

## 版本演进

| 版本 | audio | video | pts | 状态 |
|------|-------|-------|-----|------|
| v2 | decode+encode | decode+encode | fixed 累加 | ✅ 能用但有编解码延迟 |
| v3 | passthrough | passthrough | sdk timestamp | ❌ timestamp=0 没过滤 |
| v4 最终 | passthrough | passthrough+攒包 | fixed/sdk 开关 | ✅ **最终方案** |

## 最终架构（v4 全 passthrough）

```
235 FlashHead
  ↓ Carpo push (audio Opus + video H.264)
北京 Server (192.144.156.158:23800)
  ↓ Carpo pull (SDK callback)
本机 aiortc demo
  ├── _on_media callback (C 线程)
  │   ├── audio: Opus raw → call_soon_threadsafe → audio_queue
  │   └── video: NAL 攒包(SPS+PPS+IDR) → call_soon_threadsafe → video_queue
  ├── CarpoAudioTrack.recv() → av.Packet(opus) → pack() → RTP
  └── CarpoVideoTrack.recv() → av.Packet(nal) → pack() → RTP
  ↓ WebRTC
浏览器 (audio + video 同步播放)
```

## 性能对比

| 方案 | 延迟 | 视频 | 同步 |
|------|------|------|------|
| fastrtc | ~60s（缓存） | ❌ | N/A |
| aiortc v2 (decode+encode) | ~2s | ✅ | 首帧不同步 |
| **aiortc v4 (全 passthrough)** | **<1s** | ✅ | **首帧同步** |

## 相关文件

- `engine/src/voice-chat/python/aiortc_demo_v4.py` — 最终方案
- `engine/src/voice-chat/python/aiortc_demo_v3.py` — 全 passthrough（timestamp 没过滤）
- `engine/src/voice-chat/python/aiortc_demo_v2.py` — decode+encode 版
- commit: `4520c533` (v4 成功)、`a85fb205` (v2)
