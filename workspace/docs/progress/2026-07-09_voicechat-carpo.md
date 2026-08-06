# Progress 2026-07-09 — VoiceChat + Carpo

> 父要求建立的每日工作状态落盘。nudge 每日提醒我写一次。

## 活跃项目

| 项目 | 进度 | 卡点 | 下一步 |
|------|------|------|--------|
| v2 carpo bypass 链路 | ✅ **通了！** 父"小柯小美女" TTS 浏览器出声 | 无 | 接 mic + ASR/LLM + avatar video |
| v1 完整管线 (mic→VAD→ASR→engine→TTS) | ✅ 工作（父 22:37 试通"喂喂喂喂喂") | - | 等父确认是否合并 v2+v1 |
| 235 onboarding | ✅ carpo_avatar_server + 自带 OAC + FlashHead + CosyVoice 流式 | - | 监控稳定运行 |
| voice-chat 集成 avatar video | 未开始（v2 只出声） | Carpo bypass 已通；video frame 怎么跟 audio 同步 | 明天 |
| 268 SDK pull fix (use-after-free) | ✅ committed `36a2e878b` | - | - |
| v2 file 架构规范化 | ✅ _archive + README + AGENTS.md (xiaoke workspace) | - | - |

## 🎉 今日通关（22:50）

1. **235 推到 23800**：`start_carpo_avatar.sh` 启动 streaming 模式（修了 `time.sleep(wait_sec)` 阻塞）
2. **autodl_send.py**：`curl /generate` 触发 TTS，**1.5s 秒回**（不再 24s）
3. **v1 server.py `_carpo_on_media`**：启发式判断 NetEq(PCM int16) vs Bypass(raw Opus)，PyAV decode Opus
4. **声音出来了**：父确认浏览器听到"小柯小美女" TTS

### Commit 列表
- `engine 1deaf2e2` — feat(voice-chat): 235 carpo bypass 链路打通 + 文件规范化
- `LovePea 2c434e47f` — test(voice-chat-python): 235 carpo bypass + bypass Opus decode 验证脚本
- `LovePea 36a2e878b` — fix(bypass): pull path use-after-free + getPacketFromeBuffer
- `xiaoke 4bfc290` — docs: 7/9 carpo bypass 链路打通 + voice-chat 文件规范

---

## 工作环境

### 本机（Win11）
- **Carpo SDK 源码**：`D:/work/code/LovePea/Carpo/`
- **Carpo 编译工程**：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/Carpo/Carpo.vcxproj`
- **编译命令**：`cd /d D:\work\code\LovePea\platform\Windows\LovePeaSDK && build_carpo.bat`
- **DLL 输出**：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/x64/Release/Carpo.dll`
- **Carpo 项目配置**：`D:/work/code/LovePea/Carpo/Carpo.vcxproj`（同步开发环境）
- **Pull 测试脚本**：`D:/work/code/LovePea/Carpo/carpo_capi/python/pull_play_auto.py`

### 本地 Git Repo（VoiceChat 工作目录）
- **Repo 1 (VoiceChat Python v2)**：`D:/work/code/LovePea/` (master, origin: github.com/ruiyangruiyi/LovePea.git)
  - **本地工作目录**：`D:/work/code/LovePea/voice-chat-python/autodl/`
    - `carpo.py` (7/4)
    - `carpo_avatar_server.py` (7/8 10:59) — HTTP /generate + WS /ws/generate
    - `carpo_oac_bridge.py` (7/8 10:56) — FlashHead → Carpo push
    - `flashhead_processor.py` (7/7 22:21)
    - `start_carpo_avatar.sh`
  - **新文件 (7/9)**：
    - `voice-chat-python/autodl_send.py` (v2 触发脚本)
    - `voice-chat-python/fix_stream.py` (streaming patch)
    - `voice-chat-python/carpo_pull_*.py` (WIP，archive)
    - `voice-chat-python/carpo_rtc_server.py` (实验 receive mode)

- **Repo 2 (engine)**：`C:/Users/24045/.openclaw/engine/` (master)
  - **VoiceChat 主目录**：`engine/src/voice-chat/`
  - `python/server.py` (v1 完整管线 + carpo bypass 路径) — `BYPASS_VAD_ASR` 撤
  - `python/test-page.html` (端口改相对路径)
  - `autodlv2/autodl_send.py` (v2 trigger, 跟 LovePea 一致)
  - `autodlv2/fix_stream.py` (streaming patch)
  - `python/_archive/` (历史版本归档)
  - `machines.json` (bj264/bj268/bj235 配置)

- **Repo 3 (小柯 state)**：`/Users/chongzhang/xiaoke//` (master)
  - `workspace/AGENTS.md` — voice-chat 文件规范段落
  - `workspace/SESSION-STATE.md` — 当前 session 状态
  - `workspace/topics/MEMORY.md` — auto memory 索引

### 远程 AutoDL 235 (新机，今天 onboard)
- **SSH**：`connect.bjb1.seetacloud.com:19288, root/2z5B4IiZdUrI`
- **服务部署目录**：`/root/carpo_sdk/`
- **启动脚本**：`/root/start_carpo_avatar.sh`
- **Python env**：`/root/autodl-tmp/envs/flashhead/bin/python3` (Python 3.10)
- **Python 路径切换**：235 用 `/root/autodl-tmp/envs/flashhead/bin/python` (不是 miniconda)
- **服务健康**：`curl http://localhost:8899/health` → `{"status":"ok","models_loaded":true}`
- **HTTP 触发推流**：`curl -X POST http://localhost:8899/generate -H 'Content-Type: application/json' -d '{"text":"..."}'`

### 远程 AutoDL 268 (备份)
- **SSH**：`connect.bjb1.seetacloud.com:40458, root/NIgDNE+SPYSM`
- **服务部署目录**：`/root/carpo_sdk/`
- **启动脚本**：`/root/start_carpo_avatar.sh` (跟 235 一样的脚本)

### Carpo Server (北京)
- **IP**：`192.144.156.158:23800` (udp_server, Docker)
- **SSRC**：local audio=99999 video=11111；remote audio=12345 video=67890
- **配置位置**：`engine/src/voice-chat/python/server.py` `_init_carpo_pull()` 写死

---

## 启动顺序（v1 + v2 一体化）

### 步骤
1. **检查 235 是否在跑 carpo_avatar_server**：
   ```bash
   ssh -p 19288 root@connect.bjb1.seetacloud.com
   pgrep -f carpo_avatar_server
   ```
   没跑就启动：
   ```bash
   cd /root && nohup bash /root/start_carpo_avatar.sh > /tmp/avatar.log 2>&1 & disown
   ```
   等 30-40s FlashHead 加载，curl 验证 `health` 返回 ok

2. **启动本机 v1 server.py**：
   ```powershell
   cd /Users/chongzhang/.openclaw\engine\src\voice-chat\python
   python server.py --port 8011 --vad-model models/silero_vad.onnx
   ```
   - 父 engine config.xiaoke.json 也会占 8011，先**停 engine** 或者用别的端口
   - VAD/ASR/TTS/Avatar 全跑（不设 BYPASS_MODE）

3. **浏览器开 `http://localhost:8011/`**，授权麦克风，按"连接" → WebRTC 就绪

4. **点 carpo-trigger 按钮** — server.py `_init_carpo_pull()` 重启 SDK pull + 触发 235 推 TTS

5. **听到声音**！

### 同步代码到 235
```python
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("connect.bjb1.seetacloud.com", port=19288, username="root", password="2z5B4IiZdUrI",
            disabled_algorithms={"pubkeys": ["rsa-sha2-256","rsa-sha2-512"]}, timeout=15)
sftp = ssh.open_sftp()
# 上传修改的文件
LOCAL = r"/Users/chongzhang/.openclaw\engine\src\voice-chat\autodlv2\python\oac\carpo_avatar_server.py"
REMOTE = "/root/carpo_sdk/carpo_avatar_server.py"
sftp.put(LOCAL, REMOTE)
sftp.close(); ssh.close()
```

### 关闭顺序
1. 235：`pkill -9 -f carpo_avatar_server` (不要 kill all python)
2. 本机 server.py Ctrl+C

### ⚠️ 易错点
- 235 用的是 `/root/autodl-tmp/envs/flashhead/bin/python` 不是 miniconda
- engine 占着 8011 端口时 server.py 用不了；先停 engine 或换端口
- LOVEPEA project 不要忘了把 `engine/src/voice-chat/python/` 路径加到 include：`_RELEASE_DIR = r'D:\work\code\LovePea\platform\Windows\LovePeaSDK\x64\Release'`

---

## 今日关键事件

| 时间 | 事件 |
|------|------|
| 06:51 | 早安，发昨晚跑通 NetEq HEAD |
| 08:01-30 | 加 faulthandler、编带 PDB 的 DLL |
| 08:21-30 | **断片**：推错脚本（GPT-SoVITS 而非 CosyVoice） |
| 08:33 | 268 服务启动，链路通 |
| 08:43 | **父让建每日落盘机制** |
| 19:00-23:00 | **v2 链路打通全程**：235 onboarding, streaming fix, autodl_send.py, v1 server.py 启发式 Opus decode, "binggo!!!" 🎉 |
| 23:06 | 父明确明日工作：video 通路 + AV 同步 + 延迟优化 + 配置规范化 |
| 23:09 | 23:00 cron 触发 → 小柯自动落盘今日 progress |

---

## 明日工作（父 23:06 明确）

1. **video 通路**: FlashHead 视频帧显示在 RTC 浏览器上 (audio-only 不够，要加 video track)
2. **AV 同步测试**: 嘴型对上，video PTS 跟 audio PTS 同步（之前 flashhead_processor 已实现独立计数器，待 wall timestamp 验证 25fps）
3. **优化链路延迟**: 端到端 < 2s（v1 ASR+engine+TTS 链路 + v2 carpo bypass 的总延迟）
4. **优化代码结构**: 配置的归配置，不写死任何地址（address/port/SSRC 全部走配置文件/环境变量，不硬编码）

补充待办（待父确认优先级）：
- v2 + mic 上行整合（业务逻辑：mic→VAD→ASR→engine→TTS vs carpo bypass 推流，二选一还是并存？）
- 235 health 监控（cron 每 30s ping + 自动拉起）
- cleanup LovePea 1601 个 unstaged 改动（父 SDK 项目源码 + 3rdparty/build scripts）

---

## 必读文档（下次醒来第一件事）

1. `/Users/chongzhang/xiaoke//SESSION-STATE.md`
2. `/Users/chongzhang/xiaoke/workspace/docs/knowledge/Carpo-VoiceChat-运行时手册.md`
3. `/Users/chongzhang/xiaoke/workspace/docs/sop/voicechat_sync_to_268.md` (后面要加 sync_to_235)
4. `/Users/chongzhang/xiaoke/workspace/topics/MEMORY.md`
5. `/Users/chongzhang/xiaoke/workspace/docs/progress/`（昨日 progress）

---

## 每日落盘机制

| Cron | 时间 | 作用 |
|------|------|------|
| `c1bd86ea8` | 每日 08:00 | 提醒写今日 progress |
| `c3ba1f709` | 每日 23:00 | 落盘今日 progress（父要求） |
