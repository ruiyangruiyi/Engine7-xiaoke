# OAC FlashHead Processor → Carpo Push 集成研究

> 2026-07-04 小柯研究，基于 6/28-6/29 决策文档

## FlashHead Processor 输出架构

### 核心组件：`flashhead_processor.py`

```
TTS PCM (流式) → add_audio() → 攒到 audio_slice_samples (15360@16kHz)
  → _process_chunk() → FlashHead 推理 → FrameQueueItem 入队
  → _frame_collector_worker (25fps metronome) → callback 逐帧输出
```

### FrameQueueItem（音视频配对）

```python
@dataclass
class FrameQueueItem:
    video_frame: np.ndarray    # BGR uint8, (H, W, 3)
    audio_segment: np.ndarray  # float32, 24kHz, mono, 960 samples/帧
    speech_id: str
    end_of_speech: bool
```

### Callback 接口

```python
@dataclass
class FlashHeadProcessorCallbacks:
    on_video_frame: Callable[[np.ndarray], None]   # BGR frame
    on_audio_frame: Callable[[np.ndarray], None]   # float32 PCM
    on_speech_end: Callable[[str], None]
```

### 音画同步机制

**没有显式 PTS**。通过 25fps metronome 保证：
- 每帧 = 1/25 秒 = 40ms
- 每帧配 960 samples 音频（24000/25 = 960）
- audio 和 video 在同一个 FrameQueueItem 里，callback 同步调用
- idle 帧（不说话时）也发静音音频，保证 PTS 匀速前进

### 输出格式汇总

| 类型 | 格式 | 采样率/帧率 | 每帧大小 |
|------|------|------------|---------|
| 视频帧 | BGR uint8 numpy | 25fps | (H, W, 3) |
| 音频段 | float32 numpy | 24kHz mono | 960 samples/帧 |

## Carpo Push 接入方案

### 接入点：FlashHeadProcessorCallbacks

在 callback 里加一路 CarpoPushBridge：

```python
def on_video_frame(frame: np.ndarray):
    # 原有逻辑：submit_data → delegate → rtc_stream
    handler.submit_data(video=frame)
    # 新增：Carpo push
    carpo_bridge.push_video(frame)  # 需先 H.264 编码

def on_audio_frame(audio: np.ndarray):
    # 原有逻辑
    handler.submit_data(audio=audio)
    # 新增：Carpo push
    carpo_bridge.push_audio(audio, sample_rate=24000)
```

### PTS 问题

Carpo push 用 timestamp_ms 参数。需要维护一个递增的时间戳：
- 音频：每帧 960 samples / 24000 Hz * 1000 = 40ms
- 视频：每帧 40ms（25fps）
- 两者用同一个计数器：`ts_ms = frame_id * 40`

## 数据流（Carpo 集成后）

```
AutoDL (GPU)
  OAC Pipeline
    ASR → LLM → TTS (PCM 24kHz) → FlashHead → BGR frames (25fps)
      ↓ on_audio_frame              ↓ on_video_frame
      CarpoPushBridge.push_audio()  CarpoPushBridge.push_video()
        ↓ Opus encode (48kHz)        ↓ H.264 encode
        ↓                            ↓
      CarpoPusher → 北京服务器 (192.144.156.158:23800)
                        ↓
Engine (本机)
  CarpoPullBridge.on_media()
    ↓ audio: PCM 48kHz → resample 24kHz → delegate.emit()
    ↓ video: H.264 NAL → decode → delegate.video_emit()
    ↓
  fastrtc WebRTC → 浏览器
```

## 关键参数

| 参数 | 值 | 来源 |
|------|-----|------|
| TTS 采样率 | 24kHz | flashhead output_audio_sample_rate |
| 视频帧率 | 25fps | tgt_fps |
| 每帧音频 | 960 samples | 24000/25 |
| Opus 编码采样率 | 48kHz | Carpo 要求 |
| 音频重采样 | 24kHz → 48kHz | CarpoPushBridge |
| 视频编码 | H.264 (NVENC/libx264) | AutoDL 有 4090 |
| Carpo Server | 192.144.156.158:23800 | 北京服务器 |

## PTS / 丢帧处理（Carpo 内置，不需要操心）

Carpo 的 RTP 层完整处理了音画同步和丢帧：

### Push 侧（PushSenderInner）
- `getPacketTimestamp()` 把 ms 时间戳减去 baseMediaTs，转成相对时间戳
- **视频帧自动保证单调递增**：如果 `timestamp <= _lastFramePts`，自动 `_lastFramePts + 1`
- 音频和视频分别计数

### RTP 打包（RTPPaker）
- 音频 RTP clock: 48kHz (OPUS_AUDIO_SAMPLE_RATE)
- 视频 RTP clock: 90kHz (H264_VIDEO_SAMPLE_RATE)
- `calcPtsHz()` 把 ms → 各自的 RTP clock 单位

### Pull 侧（PullReceiverInner）
- `getOutPutTimeStamp()` 做时间戳重映射和同步
- 检测 PTS 回退（丢帧/乱序）→ 自动 reset timebase
- 音视频共享 `time_stamp_rebase` 基准

### 结论
**只需要传递增的 ms 时间戳**，丢帧/乱序/音画同步全由 Carpo RTP 层处理。

1. FlashHead 输出的视频帧分辨率（H, W 具体值）— 需要看配置
2. AutoDL 上 OAC 能否不装 fastrtc 启动（只用 pipeline + callback）
3. 视频编码用 NVENC（4090 硬编）还是 libx264
4. 多路输出：同一个 callback 同时走 delegate queue + Carpo push，是否有性能问题

## 相关文件

| 文件 | 说明 |
|------|------|
| `src/handlers/avatar/flashhead/flashhead_processor.py` | 核心处理器 |
| `src/handlers/avatar/flashhead/flashhead_avatar.py` | Avatar handler（注册 callback） |
| `src/service/rtc_service/rtc_stream.py` | fastrtc emit/video_emit |
| `D:/work/code/LovePea/Carpo/carpo_capi/python/carpo_bridge.py` | CarpoPushBridge 雏形 |
