# OAC WebRTC 下行管线方案

**日期：** 2026-07-01
**参与者：** 翀哥 + 小柯
**状态：** 方案评估中

## 背景

现有 voice-chat 下行走 RTMP（AutoDL FlashHead → C streamer → RTMP → SRS → 浏览器），延迟 4-7s。
新起 WebRTC 下行管线，延迟目标 < 2s。与 RTMP 管线并行，互不影响。

## 核心思路

FlashHead 推理在 AutoDL（4090 GPU），产出的音视频帧编码后通过 WebSocket 传回本地，本地 fastrtc 不解码直接塞 WebRTC track，浏览器解码。

**关键：本地是纯转发，零编解码开销。**

## 架构

```
Engine (本地 Windows)
  → LLM 生成文字回复
  → POST /voice-reply → Python server

Python server (本地)
  → ws_avatar.trigger(text) → WebSocket 发文本到 AutoDL
  → 同时收 WS 帧填充 video_queue / audio_queue
  → fastrtc AsyncAudioVideoStreamHandler
    → emit() 从 audio_queue 取 Opus 包 → aiortc audio track
    → video_emit() 从 video_queue 取 H.264 NAL → aiortc video track
  → WebRTC → 浏览器解码播放

AutoDL 4090
  → WebSocket server 收到文本
  → TTS (CosyVoice/GPT-SoVITS) 流式合成 PCM
  → FlashHead 推理 BGR 帧 (25fps, 512×512)
  → frame_collector 25fps 节拍（移植 OAC FlashHeadProcessor）
  → NVENC H.264 硬编 (PyAV, h264_nvenc, 1.5Mbps, preset p4, tune ll)
  → Opus 音频编码 (WebRTC 标准)
  → WebSocket 传 H.264 NAL + Opus 包回本地
```

## 帧格式与编码

### 视频
- FlashHead 产出：BGR uint8, 512×512, 25fps
- 编码：NVENC h264_nvenc（PyAV）
  - bitrate: 1.5Mbps
  - preset: p4, tune: ll (低延迟)
  - profile: main, rc: cbr, zerolatency: 1
- 传输：H.264 NAL 单元
- 本地：不解码，直接喂 aiortc video track → 浏览器解码

### 音频
- FlashHead 原始音频：float32, 24kHz mono
- 编码：Opus（WebRTC 标准 codec）
- 传输：Opus 包
- 本地：不解码，直接喂 aiortc audio track

### WebSocket 消息协议

```
上行（本地 → AutoDL）:
  {"type": "generate", "texts": ["句子1", "句子2"], "tts_provider": "cosyvoice"}
  {"type": "stop"}

下行（AutoDL → 本地）: 二进制帧
  [1B type][4B length BE][payload]
  
  type=0x01 视频帧: payload = H.264 NAL bytes
  type=0x02 音频帧: payload = Opus bytes  
  type=0x03 speech_end: payload = speech_id (utf-8)
```

## 工作量评估

### 新建文件

| 位置 | 文件 | 行数 | 说明 |
|------|------|------|------|
| AutoDL | `ws_stream_server.py` | ~400 | WS server + TTS + FlashHead + frame_collector + NVENC + Opus |
| 本地 | `ws_client.py` | ~200 | WS 客户端，收帧解包推入队列 |
| 本地 | `avatar/ws_avatar.py` | ~120 | 新 Avatar provider，trigger 通过 WS 发文本 |
| **总计** | | **~720** | |

### 修改文件

| 位置 | 文件 | 行数 | 说明 |
|------|------|------|------|
| 本地 | `server.py` | ~80 | Handler 改继承 AsyncAudioVideoStreamHandler，加 video_emit()，Stream 改 modality="audio-video" |
| AutoDL | `livestream_server.py` | 0 | 不动，管线1保留 |
| 本地 | `configs/xiaoke.json` | ~5 | 新增 avatar provider: "ws" |

### 可复用

- ✅ VAD → ASR → engine 链路（不动）
- ✅ SSE、/stop、/health、/avatar/config 端点
- ✅ TTS 合成逻辑（CosyVoice/GPT-SoVITS）
- ✅ FlashHead 模型加载 + 推理
- ✅ avatar 工厂模式（新增 provider）
- ✅ OAC `client_handler_rtc.py` 的 NVENC 配置代码
- ✅ OAC `FlashHeadProcessor` 的 frame_collector 25fps 节拍逻辑

## 技术参考

### OAC FlashHeadProcessor（核心参考）
- `D:/work/OpenAvatarChat/src/handlers/avatar/flashhead/flashhead_processor.py`
- frame_collector: 绝对时间基准 25fps，spin-wait 精确节拍
- FrameQueueItem: (video_frame BGR, audio_segment float32, speech_id, end_of_speech)
- idle 帧机制：环境噪声 → FlashHead 微动 + 静音音频配对

### OAC NVENC 配置
- `D:/work/OpenAvatarChat/src/handlers/client/rtc_client/client_handler_rtc.py`
- `_configure_h264_hardware_encoding()`: PyAV + h264_nvenc
- 码率 1.5Mbps, preset p4, tune ll, profile main
- 自动 fallback libx264

### OAC RtcStream（fastrtc delegate 参考）
- `D:/work/OpenAvatarChat/src/service/rtc_service/rtc_stream.py`
- `emit()` / `video_emit()` 两个独立 async coroutine
- fastrtc 底层管 WebRTC，只管调 delegate 拿数据

## 技术风险

1. **fastrtc AsyncAudioVideoStreamHandler 视频轨未验证**
   - 现有代码只用了纯音频 AsyncStreamHandler
   - 需要 modality="audio-video"，验证 fastrtc 是否支持
   - aiortc H.264 NAL 直接注入 video track 的可行性待验证

2. **AutoDL WebSocket 端口**
   - AutoDL 只映射 TCP 端口，WS 走 TCP 没问题
   - 需确认映射的端口能否被外部访问

3. **NVENC 在 AutoDL 上的可用性**
   - 4090 支持 NVENC，但需要 PyAV 编译时支持
   - OAC 已验证可用（参考配置）

4. **本地 aiortc H.264 NAL 直接注入**
   - 方案B（不解码直接塞）需要确认 aiortc API 支持
   - 备选：本地 PyAV 解码 → BGR → fastrtc（多一次解码开销）

## 方案2：Carpo RTC 服务器中转（已评估）

### Carpo 是什么
翀哥在新浪自研的 RTC 中转服务器（C++），走 UDP，标准 RTP/RTCP 协议。
- 服务端代码：`D:/work/code/carpo/`
- 客户端 SDK：`D:/work/code/LovePea/Carpo/Carpo/`

### 架构

```
浏览器(手机/PC) ──上行──→ Carpo ──→ 本地Python(ASR)
                              ↑
AutoDL FlashHead ──下行──→ Carpo ──→ 本地/浏览器
  (PushSender)              (UDP中转)   (PullReceiver)
```

### Carpo 服务端
- 核心链路：`UdpPeer recvfrom → MessageDispatcher → MediaReceiverRegister 转发`
- 信令：CMD_PUSH/CMD_PULL/CMD_UNPUSH/CMD_UNPULL（RTCP APP 包）
- 自带：NACK 丢包重传、REMB 带宽自适应、Sender/Receiver Report
- Redis/LBS/gRPC 是旁路，连不上不影响转发，不跑就行
- 唯一 Linux only：`prctl(PR_SET_NAME)` 只是设线程名，去掉不影响
- 部署：公网 Linux 服务器

### SDK 接口（干净简洁）

**PushSender（推送端，AutoDL 用）：**
```cpp
setRtcServerAddr(ip, port)
setSSRC(audioSSRC, videoSSRC, uid)
setVideoBr(bps, min, max)
startPush()
sendMediaData(type, buf, size, timestamp)  // 喂 H.264/Opus
stopPush()
```

**PullReceiver（拉流端，本地用）：**
```cpp
setRtcServerAddr(ip, port, remoteIP)
setSSRC(type, audioSSRC, videoSSRC, uid)
start()
// callback: onMediaDataRecv(type, data, len, timestamp)  // 收 H.264/Opus
stop()
```

SDK 内部处理：RTP 打包/拆包、NACK、带宽控制、拥塞控制。

### SDK 核心模块
```
LovePea/Carpo/Carpo/
├── export/          API 接口（PushSender.h, PullReceiver.h, Carpo.h）
├── src/             实现（PushSenderInner, PullReceiverInner, factory）
├── RtpRtcp/         RTP 打包/拆包、NACK、带宽估算、PacedSender
├── Network/         UDP 传输层（UdpPeer, TcpPeer, DNS）
├── AudioCodec/      音频编解码
├── webrtc/          WebRTC 组件（audio_processing, AEC, NS, VAD）
├── android/         Android 平台
├── iOS/             iOS 平台
└── 3rdparty/        第三方依赖
```

### 工作量

| 组件 | 说明 | 工作量 |
|------|------|--------|
| Carpo 服务端部署 | 编译 + 部署到公网 Linux，跳过 Redis/LBS | 小（已有代码） |
| SDK 剥离 | 去掉 UI/平台依赖，保留 RtpRtcp + Network + export 核心 | 中 |
| Python 绑定 | PushSender/PullReceiver 的 ctypes/cffi 包装 | 中 |
| AutoDL 推送端 | Python 调 PushSender .so，喂 H.264+Opus | 小 |
| 本地拉流端 | Python 调 PullReceiver .dll，收数据喂 fastrtc | 小 |

### 优势 vs 方案1

| 维度 | 方案1 WebSocket | 方案2 Carpo RTC |
|------|----------------|-----------------|
| 协议 | TCP | UDP |
| 丢包处理 | HOL blocking | NACK 重传 |
| 带宽自适应 | 无 | REMB |
| 外网支持 | 需另外解决上行 | 天然支持上下行都走中转 |
| 弱网表现 | 差 | 好 |
| 延迟 | 中 | 低 |
| 工作量 | ~750 行 Python | 编译 C++ + Python 绑定 |
| 维护 | 简单 | 重 |

### 关键判断
方案2 不仅仅是解决下行——**它同时解决了外网上行问题**。手机出门也能连，上下行都走 Carpo 中转。这是 0622 方案里"出门开会都能跟我说话"的终极形态。

## 决策：直接上 Carpo

**日期：** 2026-07-01 20:33
**理由：** RTMP 管线保底，Carpo 直接上不怕搞砸。方案2同时解决下行+外网上行。

## 下一步

1. ~~方案1评估~~ ✅ 完成
2. ~~方案2评估~~ ✅ 完成
3. ~~翀哥决策~~ ✅ 直接上 Carpo
4. 写实施计划 → 干活
