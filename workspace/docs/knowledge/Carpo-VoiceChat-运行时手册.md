# Carpo VoiceChat 运行时手册

> 2026-07-09 小柯整理（父指出我"今天早上断片了"后补的）
> 目的：下次醒来第一件事 read 这个，所有运行态/调用方式全在这里

---

## 1. 服务器/机器清单

| 机器 | 用途 | SSH | 备注 |
|------|------|-----|------|
| 本机（Win11） | Carpo SDK 编译 + Pull 端测试 | localhost | `D:/work/code/LovePea/` |
| AutoDL 268 (RTX 4090) | Push 端（CosyVoice TTS + FlashHead + Carpo push） | connect.bjb1.seetacloud.com:40458, root/NIgDNE+SPYSM | `/root/carpo_sdk/` |
| 北京 server | Carpo Server (UDP) | - | 192.144.156.158:23800（udp_server） |

---

## 2. 268 上的服务

### 2.1 carpo_avatar_server.py

**位置**：`/root/carpo_sdk/carpo_avatar_server.py`（7/8 已部署，16KB）

**功能**：
- 文字 → CosyVoice 流式 TTS → FlashHead processor → Carpo push
- 同时通过 WebSocket 推 H.264 + Opus raw bytes 给连进来的客户端

**接口**：
| 端点 | 类型 | 用途 |
|------|------|------|
| `POST /generate` | HTTP | body `{"text": "...", "tts_provider": "cosyvoice"}` → 同步推完 |
| `WS  /ws/generate` | WebSocket | 发文字 → 收 H.264 NAL (tag=0) + Opus (tag=1) raw bytes |
| `GET  /health` | HTTP | 健康检查 |
| `POST /shutdown` | HTTP | 优雅关闭 |

**SSRC 配置**（已硬编码在 server）：
- audio SSRC: 12345
- video SSRC: 67890
- uid: avatar_push

**启动命令**：
```bash
ssh -p 40458 root@connect.bjb1.seetacloud.com
cd /root/carpo_sdk
export DASHSCOPE_API_KEY="sk-..."         # 父自己填
export CARPO_SERVER=192.144.156.158        # 默认就是这个
nohup python3 carpo_avatar_server.py --port 8899 > avatar.log 2>&1 &
```

**调用示例**（本机）：
```bash
curl -X POST http://localhost:8899/generate \
    -H "Content-Type: application/json" \
    -d '{"text": "你好测试"}'
```

**循环调用脚本**（不停推）：
```bash
while true; do
  curl -s -X POST http://localhost:8899/generate \
    -H "Content-Type: application/json" \
    -d '{"text":"你好 这是一个循环测试"}'
  sleep 5
done
```

**注意**：
- 父已经 7/8 部署好了，不要重写脚本
- 现在没在跑（7/9 早 ps 看了，只有 jupyter/tensorboard），需要启动
- 启动后等 10-30 秒 FlashHead pipeline 加载

### 2.2 文件清单（268 /root/carpo_sdk/）
```
carpo.py                         # ctypes bindings
carpo_avatar_server.py           # 主服务（POST /generate + WS /ws/generate）
carpo_oac_bridge.py              # FlashHead → Carpo push 桥
carpo_bridge.py                  # （旧版本？）
flashhead_processor.py           # FlashHead 处理逻辑（从 OAC 搬）
libcarpo.so                      # 编译好的 SDK 库
flash_head/                      # FlashHead pipeline 代码
```

### 2.3 Python 环境
- flashhead env: `/root/autodl-tmp/envs/flashhead/bin/python3` (Python 3.10)
- gptsovits env: `/root/autodl-tmp/envs/gptsovits/bin/python3`
- 默认用 flashhead

---

## 3. 本机（Win11）Pull 端

### 3.1 SDK 路径
- 源码：`D:/work/code/LovePea/Carpo/`
- 编译工程：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/Carpo/`
- 编译脚本：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/build_carpo.bat`
- DLL 输出：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/x64/Release/Carpo.dll`
- PDB（必须保留！）：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/Carpo/x64/Release/Carpo.pdb` (9.5MB)

### 3.2 Pull 测试脚本
- `D:/work/code/LovePea/Carpo/carpo_capi/python/pull_play_auto.py`

**配置**：
```python
puller.set_ssrc(carpo.SSRC_LOCAL, 99999, 11111, 'audio_test')      # local
puller.set_ssrc(carpo.SSRC_REMOTE, 12345, 67890, 'audio_test')     # remote（=268 push 端）
puller.set_server('192.144.156.158', 23800, remote_ip='106.39.200.204')
```

**启动**：
```bash
cd D:\work\code\LovePea\Carpo\carpo_capi\python
python.exe .\pull_play_auto.py 2> crash.log
```

**已加 faulthandler**（崩了 stderr 有 native traceback）。

### 3.3 编译
```bash
cd D:/work/code/LovePea/platform/Windows/LovePeaSDK
cmd.exe //c "build_carpo.bat"
```
- Release|x64 已配 `/Zi /DEBUG`（7/9 早加的）→ 出 Carpo.pdb
- HEAD 当前是 NetEq 模式（bypass 改动在 stash@{0}）

---

## 4. 端到端调试流程

```
268 push:    carpo_avatar_server.py (HTTP POST /generate)
                → CosyVoice 流式 TTS → FlashHead → carpo_oac_bridge.push_audio/push_video
                → libcarpo.so → UDP 192.144.156.158:23800

server:      media_receiver → 转发给 pull

本机 pull:   pull_play_auto.py → Carpo.dll → audio/video callback
```

**验证步骤**：
1. 启动 268 服务（2.1 命令）
2. 调用 /generate 推一次流（curl）
3. 启动本机 pull 端（3.2 命令）
4. 看 `[XK_ATS] audio ms_ts=` 和 `[XK_VTS] video ms_ts=` 日志
5. 期望：audio 持续收到，video 持续收到，SPS 后视频帧出来

---

## 5. 当前卡点（7/9 早）

| 卡点 | 状态 | 备注 |
|------|------|------|
| Pull audio 尖峰噪音 | 调研方案 C 旁路已写，stash@{0} | HEAD 跑 NetEq 链路 OK 收 500 真包 |
| AV pts 同步 | 独立 _video_pts + _audio_pts 已实现 | 待 frame_collector wall timestamp 验证 25fps |
| voice-chat 集成 Carpo | 未做 | 替代 WebRTC 接入 |

---

## 6. SSH/paramiko 工具

```python
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("connect.bjb1.seetacloud.com", port=40458, username="root", password="NIgDNE+SPYSM",
            disabled_algorithms={"pubkeys": ["rsa-sha2-256","rsa-sha2-512"]},
            timeout=15)
```

注意：`disabled_algorithms` 是必须加的，不然 OpenSSH 新算法不通。

---

## 7. 调试工具栈

| 工具 | 用途 |
|------|------|
| faulthandler | Python 看 DLL native crash traceback |
| Carpo.pdb | Release+x64 /Zi /DEBUG 解 native frame 偏移 |
| MeetingLog.dll | Carpo 日志 (PRINT_ALL=0x1111) |
| OutputDebugString | 替代 printf 不阻塞（Windows DLL） |

---

## 8. 关键文件改动记录

- 7/8 早：AudioRTPReceiver.cpp/.hpp 加 XK_OPUS_BYPASS 方案 C → stash@{0}
- 7/8 晚：纯净 HEAD + faulthandler + /Zi /DEBUG → 编出带 PDB DLL
- 7/9 早：vcxproj 加 `<DebugInformationFormat>ProgramDatabase</DebugInformationFormat>`，Carpo.pdb 9.5MB

---

## 9. 我犯过的错（避免再犯）

1. ❌ 推 `_loop_tts_demo.py` 上 268（多余，已有 carpo_avatar_server.py）
2. ❌ 记成 GPT-SoVITS（实际是 CosyVoice API）
3. ❌ 说"啥也不记得"（应该主动 read docs/）
4. ✅ 改：每次会话开始必须 read SESSION-STATE + 这份运行时手册

---

## 10. 下次醒来第一件事

1. read `/Users/chongzhang/xiaoke//SESSION-STATE.md`
2. read 本文件（运行时手册）
3. 看一下 HEARTBEAT/最近消息（父在聊什么）
4. **不要凭印象回答，先看文档**