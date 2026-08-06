# Voice-Chat 项目环境文档

> 类似 CC 的单一工作目录规范。不再随意起目录。

## 目录结构

```
engine/src/voice-chat/
├── python/                    ← 本机 runtime（唯一）
│   ├── server.py              # VAD→ASR→Engine→TTS 主服务
│   ├── carpo_pull_server.py   # bypass pull → fastrtc → 浏览器
│   ├── carpo_pull_handler.py  # pull handler（Opus decode + emit）
│   ├── vad.py / asr.py        # 语音识别
│   ├── tts/                   # TTS providers
│   ├── avatar/                # avatar providers
│   └── models/                # ONNX 模型
├── autodlv2/                  ← 268 AutoDL 部署源码（唯一）
│   ├── python/oac/
│   │   ├── carpo_avatar_server.py   # FastAPI: /generate + /ws/generate
│   │   ├── carpo_oac_bridge.py      # FlashHead → Carpo push 桥
│   │   └── flashhead_processor.py   # FlashHead 推理
│   └── config/                # 配置文件
└── local/                     ← 工具脚本（SSH 管理）
    ├── livestreamctl.py
    ├── livestream_send.py
    └── srsctl.py
```

## 机器信息

| 机器 | IP/SSH | 用途 |
|------|--------|------|
| **本机 (Win11)** | localhost | VAD/ASR 推理 + Carpo pull + fastrtc |
| **AutoDL 268** | `connect.bjb1.seetacloud.com:40458`, root/NIgDNE+SPYSM | FlashHead + Carpo push |

### 268 环境
- **Python venv**: `/root/autodl-tmp/envs/flashhead/bin/python3` (Python 3.10)
- **部署路径**: `/root/carpo_sdk/`
- **启动脚本**: `/root/start_carpo_avatar.sh`
- **DashScope API key**: 写死在 start 脚本里

## 同步规则

- **runtime 不改 268 代码**，部署代码不改 runtime 代码
- 改 268 代码 → 改 `autodlv2/python/oac/` → sftp 到 `/root/carpo_sdk/` → 重启 268
- `LovePea/voice-chat-python/autodl/` 是 git 同步镜像，每次改完从 autodlv2 同步过去 git commit

## Git repo

```
D:/work/code/LovePea/          (git master)
└── voice-chat-python/autodl/  # 268 部署代码镜像（git 管理）
```
