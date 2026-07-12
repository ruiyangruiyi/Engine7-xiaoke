# AutoDL 推流服务方案（Carpo 版）

> 2026-07-04 翀哥确认架构

## 背景

livestream_server.py 的 TTS→FlashHead 接口是 **WAV 文件**（非流式，延迟高）。
OAC 的 flashhead_processor 是**流式**的（add_audio 攒够就推理，延迟低）。

用 OAC 的流式 processor 替代 WAV 方式，输出接 CarpoPushBridge。

## 架构

```
本机 engine 回复文字
    ↓ HTTP POST（类似 livestream_send.py）
AutoDL: carpo_avatar_server.py (:8899)
    ↓ 文字 → CosyVoice 流式 TTS → PCM chunks
    ↓ PCM chunks → flashhead_processor.add_audio()
    ↓ processor callback → CarpoPushBridge.push_audio/push_video
    ↓
CarpoPusher → 北京服务器 → 本机 CarpoPullBridge → 浏览器
```

## 关键区别 vs livestream_server.py

| 维度 | livestream_server.py | carpo_avatar_server.py |
|------|---------------------|----------------------|
| TTS→FlashHead 接口 | WAV 文件 | 流式 PCM (flashhead_processor.add_audio) |
| 传输 | RTMP → SRS | Carpo push → Carpo Server |
| TTS | GPT-SoVITS (本地) | CosyVoice (百炼 API) |
| 延迟 | 高（等整段 WAV） | 低（流式，攒够 24 帧就推理） |

## 接口设计

### AutoDL 服务 (carpo_avatar_server.py)

```
POST /generate
  Body: {"text": "你好", "tts_provider": "cosyvoice"}
  → CosyVoice 流式 TTS → FlashHead processor → Carpo push
  Response: {"ok": true, "job_id": "xxx"}

GET /health
  → {"status": "ok", "models_loaded": true}

POST /shutdown
  → graceful shutdown
```

### 本机调用（替代 livestream_send.py）

engine 回复后，POST 文字到 AutoDL 的 `/generate`，跟之前一样走 SSH。

## 依赖

AutoDL 上需要（flashhead 环境）：
- FlashHead pipeline（已有）
- flashhead_processor.py（从 OAC 搬）
- CarpoPushBridge（已写好）
- CosyVoice / dashscope SDK（已装）
- FastAPI（已装）

不需要：OAC demo.py、ASR、VAD、fastrtc、aiortc
