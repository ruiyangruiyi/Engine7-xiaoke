# Carpo SDK 关键参数备忘

**日期：** 2026-07-05

## 验证过的参数

### Push 端 (AutoDL)

| 参数 | 值 | 说明 |
|------|-----|------|
| server IP | 192.144.156.158 | 北京腾讯云 |
| server port | 23800 | UDP 数据端口 |
| audio SSRC | 12345 | push 端音频流标识 |
| video SSRC | 67890 | push 端视频流标识 |
| uid | audio_test / av_test | 用户标识 |
| audio codec | Opus 48kHz mono | TTS PCM 24kHz → resample 48kHz → Opus |
| audio frame | 960 samples / 20ms | Opus 编码帧大小 |
| video codec | H.264 Baseline | PyAV libx264 |
| video GOP | 48 frames (2s @ 24fps) | 匹配 Android MediaCodec |
| video bitrate | 500K-1Mbps | |

### Pull 端 (Windows)

| 参数 | 值 | 说明 |
|------|-----|------|
| local audio SSRC | 99999 | pull 端自身标识 |
| local video SSRC | 11111 | |
| remote audio SSRC | 12345 | 匹配 push 端 |
| remote video SSRC | 67890 | 匹配 push 端 |

### Carpo Server (北京 Docker)

| 参数 | 值 |
|------|-----|
| 容器 | carpo_server 5b2f93c4fdab |
| 镜像 | carpo-server:latest |
| UDP | 0.0.0.0:23800 |
| Redis | 127.0.0.1:36379 |

## NetEq 输出格式

| 属性 | 值 | 说明 |
|------|-----|------|
| 采样率 | 48000 Hz | config_.sample_rate_hz |
| 声道 | stereo (2ch) | interleaved L,R,L,R... |
| 每包大小 | 1920 bytes | 960 stereo frames × 2 bytes |
| 每包时长 | 20ms | 960 samples / 48000 Hz |
| 解码后 | PCM int16 | NetEq 内部 Opus→PCM |

**注意：** stereo[::2] 提取左声道得 480 samples（10ms @ 48kHz），不是 960。

## RTP Payload Type

| 类型 | PT 值 | 定义 |
|------|-------|------|
| H.264 | 107 | H264_90000_PT |
| Opus | 111 | OPUS_48000_PT |
| AAC | 113 | AAC_48000_PT |
| VP8 | 100 | VP8_90000_PT |

push 端 `RTP_PAYLOAD_VIDEO_H264 = (1<<16) | 107`，RTP 包里实际 PT = 107（mask 后）。

## 采样率转换链

```
TTS 输出: PCM 24kHz mono int16
  → resample_poly(pcm, 48000, 24000) → PCM 48kHz
  → Opus 编码 (48kHz mono, frame_size=960)
  → Carpo push (Opus bytes)
  → Server 转发
  → Carpo pull → NetEq 解码
  → PCM 48kHz stereo int16 (1920B/packet)
  → stereo[::2] → PCM 48kHz mono (480 samples)
  → resample_poly(mono, 24000, 48000) → PCM 24kHz mono (240 samples)
  → buffer 累积到 480 samples
  → fastrtc emit (24kHz, 480 samples/frame)
  → 浏览器
```

## auto memory

这是参考性质的参数表，不是 auto memory 项。参数值可能随配置变化。
