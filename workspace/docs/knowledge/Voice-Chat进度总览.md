# Voice-Chat 进度总览

**更新日期**：2026-07-02 20:15

## 项目目标

搭建完整的实时语音聊天管线，接入 Carpo 实时音视频 SDK。

## 整体架构

```
浏览器 ──WebRTC──→ server.py (:8011)
                      │
                   VAD (Silero) → ASR (SenseVoice zh)
                      │
                   POST /webhook/voice-chat → Engine (TS)
                      │
                   Engine: LLM + 记忆 + 工具
                      │
                   回复 ← POST /voice-reply (:8011)
                      │
                ┌───────┴───────┐
                │ TTS (本地)    │ Avatar (AutoDL)
                │ CosyVoice     │ FlashHead → RTMP 推流
                └───────────────┘
                      │
                   Carpo SDK (RTP/RTCP over UDP)
                      │
                   Carpo Server (Docker :23800)
```

## 当前状态

### ✅ 已完成

| 模块 | 状态 | 说明 |
|------|------|------|
| server.py | ✅ 运行中 | 完整 VAD→ASR→Engine→TTS 管线 |
| VAD (Silero) | ✅ | 语音端点检测 |
| ASR (SenseVoice) | ✅ | 中文语音识别 |
| Engine 桥接 | ✅ | webhook 双向通信 |
| TTS (CosyVoice) | ✅ | 百炼流式合成 |
| Avatar (FlashHead) | ✅ | AutoDL GPU 推流 |
| Carpo SDK 编译 | ✅ 7/2 | VS2022 v143, 175 源文件 |
| Carpo C Wrapper | ✅ 7/2 | 8 个 extern "C" 函数导出 |
| Python ctypes 绑定 | ✅ 7/2 | CarpoPusher 类 |
| Carpo Server Docker | ✅ 7/2 | udp_server 跑通 23800/udp |
| 推流验证 | ✅ 7/2 | 真实 UDP 通信 + 事件回调 |
| 新浪痕迹清理 | ✅ 7/2 | URL + 凭据 + 镜像名 |
| autodlv2 部署包 | ✅ 7/2 | TTS+Avatar+livestream 整理 |

### 🔲 待做

| 模块 | 优先级 | 说明 |
|------|--------|------|
| PullReceiver C Wrapper | 高 | 拉流端（接收远端音频/视频） |
| 真实 Opus 推流 | 高 | 推真实编码音频，验证音质 |
| 双向推拉流测试 | 高 | 推流+拉流同时跑 |
| voice-chat 集成 | 高 | Carpo 替代 WebRTC 接入 |
| AEC/AGC/NS | 中 | 双向语音时需要（调参工作量大） |
| Carpo Server 公网部署 | 中 | Docker 到公网，多用户接入 |
| 多房间路由 | 低 | 服务端改 Redis 路由 |

## 文件索引

### Carpo SDK + C Wrapper
- 编译指南：`docs/knowledge/Carpo-SDK编译指南.md`
- C Wrapper 接口：`docs/knowledge/Carpo-C-Wrapper-ctypes接口.md`
- Docker 部署：`docs/knowledge/Carpo-Server-Docker部署.md`
- 新浪清理记录：`docs/decisions/2026-07-02_新浪痕迹清理记录.md`

### Voice-Chat 代码
- 主目录：`engine/src/voice-chat/`
- Python 管线：`engine/src/voice-chat/python/server.py`
- TTS：`engine/src/voice-chat/python/tts/`
- Avatar：`engine/src/voice-chat/python/avatar/`
- 部署包：`engine/src/voice-chat/autodlv2/`

### Carpo 源码
- SDK：`D:/work/code/LovePea/Carpo/Carpo/`
- C Wrapper：`D:/work/code/LovePea/Carpo/carpo_capi/`
- 编译工程：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/Carpo/`

## 关键技术决策

1. **C Wrapper 而非 SWIG/pybind**：extern "C" 最简单，ctypes 直接用，零依赖
2. **AEC/AGC/NS 暂不编**：推流端用不着，双向语音时再加回来
3. **Docker 不改服务端代码**：原服务端代码够用，只改 SDK 端
4. **Redis 本地化**：容器内装 redis-server，不依赖外部 Redis 集群
