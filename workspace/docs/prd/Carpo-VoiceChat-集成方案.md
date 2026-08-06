# Carpo Voice-Chat 集成方案

> 2026-07-03 小柯起草，翀哥确认架构方向

## 目标

### 短期（当前）
OAC WebRTC 方案打通 → 电脑上与硅基人实时音视频通信

### 中期
- 手机外网视频电话/会议
- 浏览器/微信小程序 1v1 或 NvN 连麦
- **人 vs 硅基人** / **硅基人 vs 硅基人**（业界首创）

## 架构

```
AutoDL (GPU 节点)                         Engine (前端服务节点)
┌──────────────────────────┐              ┌─────────────────────────────┐
│ OpenAvatarChat Pipeline   │              │ 浏览器 (标准 WebRTC)          │
│                           │              │   ↕ fastrtc                  │
│ ASR → LLM → TTS → PCM     │              │   ↕ RtcStream delegate       │
│            Avatar → BGR帧  │              │                              │
│                           │   Carpo       │ CarpoPullBridge              │
│ CarpoPushBridge           │── push ──→   │   ↓ on_media (PCM 48kHz)    │
│   ↓ Opus encode           │              │   ↓ resample → delegate      │
│   ↓ H.264 encode          │              │   ↓ emit() / video_emit()    │
│   → CarpoPusher           │              │   → 浏览器播放                 │
│   → Carpo Server (Docker) │←─ pull ───   │ CarpoPuller                  │
│                           │              │                              │
└──────────────────────────┘              └─────────────────────────────┘
                                            未来: relay → 小程序/webview
```

## 为什么用 Carpo 做中间层

1. **浏览器端保留标准 WebRTC** — 所有浏览器原生支持，不用做播放器
2. **微信小程序 webview** — 大概率支持 WebRTC，通用性好
3. **AutoDL↔Engine 分离** — GPU 推理节点和前端服务节点可以部署在不同机器
4. **Fan-out 能力** — 一路 push，多路 pull（relay），支持 NvN 场景
5. **低延迟** — UDP 传输，比 HTTP streaming 快

## 分工

### AutoDL 端（Push 侧）
- OpenAvatarChat 的 TTS 输出 PCM (24kHz) → CarpoPushBridge.push_audio()
- Avatar 输出 BGR 帧 → H.264 编码 → CarpoPushBridge.push_video()
- CarpoPusher → Carpo Server (Docker)

### Engine 端（Pull 侧）
- CarpoPuller 收到 PCM (48kHz s16 mono) → 重采样到 24kHz
- 喂给 RtcStream delegate 的 output queue
- fastrtc 的 emit() / video_emit() 从 queue 取数据 → 浏览器 WebRTC

### 浏览器端
- **不改** — 继续用 fastrtc Stream + AsyncAudioVideoStreamHandler
- 浏览器看到的还是标准 WebRTC，不知道中间有 Carpo

## 数据格式

### 音频
| 环节 | 格式 | 采样率 | 声道 |
|------|------|--------|------|
| TTS 输出 | PCM s16 | 24kHz | mono |
| CarpoPushBridge 编码 | Opus | 48kHz | mono |
| Carpo Server 传输 | Opus (RTP) | 48kHz | mono |
| CarpoPullBridge 回调 | PCM s16 (NetEq 解码) | 48kHz | mono |
| delegate input | PCM s16 | 24kHz (resample) | mono |
| fastrtc emit | PCM | output_sample_rate | mono |

### 视频
| 环节 | 格式 | 说明 |
|------|------|------|
| Avatar 输出 | BGR numpy | 需编码为 H.264 |
| CarpoPushBridge | H.264 NAL | push_video() |
| CarpoPullBridge | H.264 NAL | 需解码为帧 |

## 已完成

| 日期 | 里程碑 | 状态 |
|------|--------|------|
| 7/2 | Carpo C wrapper (PushSender) 编译+推流验证 | ✅ |
| 7/3 | PullReceiver C wrapper 编译+测试 | ✅ |
| 7/3 | 真实 Opus 端到端推拉 (151帧推/286帧收) | ✅ |
| 7/3 | 双向推拉+人耳验证 (576帧, 440Hz sine) | ✅ |
| 7/3 | Windows wheel 打包 (carpo-audio-0.1.0) | ✅ |
| 7/3 | Linux libcarpo.so 编译 (176文件, Docker验证) | ✅ |
| 7/3 | CarpoBridge 雏形 (PushBridge + PullBridge) | ✅ |
| 待定 | AutoDL 部署 push 侧 | 🔲 |
| 待定 | Engine 端 pull → delegate 桥接 | 🔲 |
| 待定 | 端到端联调 | 🔲 |

## 关键技术发现

### PullReceiver 返回 PCM 不是 Opus
Carpo PullReceiver 内部自带 NetEq 解码器，on_media 回调返回的是 raw PCM (s16, mono, 48kHz)，不是 Opus 包。这简化了 pull 侧代码——不需要额外解码。

### set_server 返回 -1 不是错误
UDP 是无连接协议，connectToMediaServer 返回异步状态码 -1。实际推拉正常工作。

### 需要非零 video SSRC
Carpo Server 需要 audio_ssrc 和 video_ssrc 都非零才能建立会话。即使只推音频也要设 video_ssrc。

## 待解决

1. **delegate 接口对接** — 需要确认 `put_data(EngineChannelType.AUDIO, ...)` 的确切调用方式
2. **视频编码** — Avatar BGR → H.264，AutoDL 上用 NVENC 还是 libx264？
3. **Carpo Server 部署** — Docker 在本机还是 AutoDL？Engine 怎么连？
4. **relay 方案** — 多端 fan-out 怎么实现？

## 相关文件

| 文件 | 说明 |
|------|------|
| `Carpo/carpo_capi/carpo_capi.h` | C ABI 头文件 |
| `Carpo/carpo_capi/carpo_capi.cpp` | C ABI 实现 |
| `Carpo/carpo_capi/python/carpo.py` | Python ctypes 绑定 |
| `Carpo/carpo_capi/python/carpo_bridge.py` | OAC 集成桥接层 |
| `Carpo/carpo_capi/python/test_carpo_2way.py` | 双向推拉测试 |
| `Carpo/carpo_capi/build.sh` | Linux 编译脚本 |
| `Carpo/carpo_capi/setup.py` | Win wheel 打包 |
