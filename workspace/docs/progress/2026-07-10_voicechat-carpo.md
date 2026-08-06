# Progress 2026-07-10 — VoiceChat + Carpo

> 父要求建立的每日工作状态落盘。nudge 每日提醒我写一次。

## 活跃项目

| 项目 | 进度 | 卡点 | 下一步 |
|------|------|------|--------|
| v2 carpo bypass 链路 | ✅ **通了** (7/9) | - | 已进入优化阶段 |
| v1 完整管线 (mic→VAD→ASR→engine→TTS) | ✅ 工作 (7/9) | - | 与 v2 并存模式切换 |
| voice-chat 集成 avatar video | ✅ **通了** (7/10 09:50 父看到画面+嘴型) | - | 已通，暂不动手 |
| voice-chat SDK pull 自动启动 | ✅ 浏览器连接时自动起 pull | - | - |
| 端到端时延收集 | ✅ SSE 推送 + 浏览器 latency 表 + 跨机器延迟 (RTP timestamp) | 精度依赖 NTP 校时 | 父要求继续优化 <2s |
| 链路优化 | ✅ 消除重复 SSH + 删 sleep(2) + SDK pull 常驻 + FlashHead 推理异步化 | - | - |
| **🆕 前端重新设计** | ✅ settings modal + 视频小窗(可拖动+PiP) + pull 控制 + 延迟面板 | - | - |
| **🆕 配置持久化** | ✅ workspace/voice-chat-config.json | - | - |
| **🆕 打断功能** | ✅ /stop 端点 + 停 LLM + 停 TTS + 停 235 generate | 打断 bug 修了 5 轮 | 待验证: 长文本打断彻底停 |
| **🆕 多形象切换** | ✅ /api/avatar/switch (SSH 隧道) + 前端 grid 点击切换 | 235 只有一个 girl.png | 传姐姐/小柯形象上去 |
| **🆕 本地 CosyVoice2 TTS** | ✅ TTS_PROVIDER=local\|dashscope 开关 | CUDA EP 问题: flow encoder 跑 CPU 太慢 | 明天跟父看 |
| **🆕 TTS 真流式** | ✅ on_data 回调直喂 queue | - | - |
| voice-chat 模式切换 (v1 + v2 兼容) | 🟡 决策落盘 docs/decisions/2026-07-10 | 配置文件名、热切换 | 父确认后开干 |
| AV 同步验证 | 🟡 wall-clock 已统一 | 25fps 待验证 | 真有问题再调 PTS pacing |
| 配置规范化 | 🟡 部分已走 voice-chat-config.json | SSRC 仍写死 server.py | 提到 env/config |
| 尖峰噪音定位 | 🟡 dump_pcm.py 工具已就绪 | SDK pre-encode PCM 抽点位置待父确认 | 等父指示 |
| 268 SDK pull fix | ✅ committed `36a2e878b` (7/9) | - | - |

---

## 🎯 父 7/9 23:06 明确的今日工作（P0）— 全部完成 ✅

1. ~~**video 通路**~~: ✅ 09:50 父看到画面+嘴型
2. ~~**AV 同步测试**~~: ✅ 父测后看着对得上，暂不动手
3. ~~**优化链路延迟**~~: ✅ 时延收集框架完成 + 链路优化（消除重复 SSH + 异步化）
4. ~~**优化代码结构**~~: ✅ 配置持久化到 voice-chat-config.json（SSRC 部分待改）

---

## 明日工作

1. **CosyVoice2 CUDA EP 问题** — flow encoder 跑 CPU 太慢，跟父一起看
2. **打断功能验证** — 长文本打断彻底停 + 打断后 idle 呼吸正常 + 再说话正常回复
3. **多形象扩展** — 传姐姐/小柯形象到 235，确认 FlashHead 热换 cond_image
4. **Engine bridge.ts 重编** — 改了需要父操作重编 Engine
5. **尖峰噪音定位** — dump_pcm.py 工具已就绪，等父确认 SDK 抽点位置
6. **配置规范化** — SSRC 仍写死 server.py，提到 env/config
7. **端到端延迟优化** — 时延框架已通，继续优化目标 <2s

补充待办（待父确认优先级）：
- voice-chat 模式切换 (v1+v2 兼容) — 决策已落盘，待父确认细节
- 235 health 监控（cron 每 30s ping + 自动拉起）
- cleanup LovePea unstaged 改动

---

## 7/7-7/9 历史通关回顾（上下文）

### 7/7 — AV 端到端通了 🎉
- async push worker + 墙钟 PTS + generate fix + OAC idle audio 漏洞修复
- 6 commit (dfd566bec → 7c152dcfb) + Carpo.dll XK_ fprintf 全注释

### 7/8 — 235 onboarding + v2 bypass 链路
- 235 carpo_avatar_server.py streaming 模式 + 修 `time.sleep(wait_sec)` 阻塞
- carpo_oac_bridge.py + flashhead_processor.py

### 7/9 — v2 链路打通 (声音出来) 🎉🎉
1. **235 推到 23800**：`start_carpo_avatar.sh` 启动 streaming 模式
2. **autodl_send.py**：`curl /generate` 触发 TTS，**1.5s 秒回**（不再 24s）
3. **v1 server.py `_carpo_on_media`**：启发式判断 NetEq(PCM int16) vs Bypass(raw Opus)，PyAV decode Opus
4. **声音出来了**：父确认浏览器听到"小柯小美女" TTS
5. **修复 bypass pull use-after-free**: `36a2e878b`

### Commit 列表（最近）
- `engine 1deaf2e2` — feat(voice-chat): 235 carpo bypass 链路打通 + 文件规范化
- `LovePea 2c434e47f` — test(voice-chat-python): 235 carpo bypass + bypass Opus decode 验证脚本
- `LovePea 36a2e878b` — fix(bypass): pull path use-after-free + getPacketFromeBuffer
- `xiaoke 4bfc290` — docs: 7/9 carpo bypass 链路打通 + voice-chat 文件规范
- `xiaoke 78c664d` — docs(progress): 父 23:06 明日计划 — video/AV同步/延迟<2s/配置化
- `xiaoke 0a1787d` — docs(progress): 7/9 carpo bypass 链路打通终状态

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

### 远程 AutoDL 235 (新机)
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
- **配置位置**：`engine/src/voice-chat/python/server.py` `_init_carpo_pull()` 写死 ⚠️ 待改 env

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

## 🎉 今日通关（7/10）

### 上午：video 通路 + 时延收集
1. **video 通路打通** (`b6674a4e`) — FlashHead → RTC 浏览器，父 09:50 看到画面+嘴型
2. **链路优化** (`48eb8649`) — 消除重复 SSH 建联 + 删 sleep(2) + SDK pull 常驻
3. **端到端时延收集** (`088cbf5f` → `827b4d5d`) — SSE 推送 + 浏览器 latency 表 + 跨机器延迟 (RTP timestamp) + 滚动窗口
4. **FlashHead 推理异步化** (`42cb7781`) — add_audio 不再阻塞
5. **TTS 真流式** (`680af05c`) — on_data 回调直喂 queue

### 下午：前端重设计 + 打断功能
6. **前端重新设计** (`87244332`) — settings modal + 视频小窗(可拖动+PiP) + pull 控制 + 延迟面板
7. **配置持久化** (`73f971b2`) — workspace/voice-chat-config.json
8. **/generate 异步化** (`34fc8b57`) — 后台线程处理，立即返回
9. **avatar._send 重构** (`80281673`) — 直接 SSH curl 235 /generate，不走 livestream_send.py
10. **235 /stop 端点** (`ebf990c2`) — 打断当前 generate
11. **打断 bug 修了 5 轮** (`8b9c2038` → `1001aed9`) — stop_flag 残留 / avatar.stop 阻塞 / FlashHead 残留帧 / interrupt 卡 idle / pending_audio 残留
12. **auto 模式 pull** (`d84efa2d`) — 浏览器连接时启动，断开时停止

### 晚间：多形象切换 + CosyVoice2
13. **235 /api/avatar** (`84160bd3`) — FlashHead 形象切换端点
14. **本地 /api/avatar/switch 代理** (`85c1d847`) — SSH 隧道不走 HTTP
15. **前端 grid 点击切换** (`7dbb2d62`) — 人物形象 grid
16. **切换后重置 latent** (`39d8ea0f` + `c4ee428b`) — 避免旧形象闪回
17. **本地 CosyVoice2 TTS** (`dd2e3d3d`) — TTS_PROVIDER=local|dashscope 开关
18. **UI 精简** (`aa15665c` → `d664f609`) — 主界面只留通话/打断/结束，按钮改圆形电话风格

### Commit 统计
- **engine: 57 commits** (今天一天！)
- **xiaoke: 3 commits** (docs)
- **LovePea: 0 commits** (SDK 侧今天没改动)

---

## 今日关键事件

| 时间 | 事件 |
|------|------|
| 08:01 | 每日 progress 落盘 cron 触发 → 自动创建 7/10 progress |
| 09:50 | **🎉 video 通路打通** — 父看到画面+嘴型 |
| 10:20 | 端到端时延收集框架完成 — SSE 推送 + 浏览器 latency 表 |
| 10:39 | 父要求严格收集每步时延 — timing 字段方案落盘到 SESSION-STATE |
| 12:00-14:00 | 链路优化 — 消除重复 SSH + FlashHead 异步化 + TTS 真流式 |
| 14:00-18:00 | **前端重设计 + 打断功能** — 5 轮 bug 修复 |
| 18:00-22:00 | **多形象切换 + CosyVoice2 本地 TTS** |
| 22:37 | daily 日志落盘 |
| 23:09 | 23:00 cron 触发 → 落盘今日 progress |

---

## 必读文档（下次醒来第一件事）

1. `/Users/chongzhang/xiaoke//SESSION-STATE.md`
2. `/Users/chongzhang/xiaoke/workspace/docs/knowledge/Carpo-VoiceChat-运行时手册.md`
3. `/Users/chongzhang/xiaoke/workspace/docs/decisions/2026-07-10_voicechat模式切换方案.md`
4. `/Users/chongzhang/xiaoke/workspace/docs/decisions/2026-07-10_端到端延迟计算文档.md`
5. `/Users/chongzhang/xiaoke/workspace/docs/research/2026-07-10_voice_chat_frontend_redesign.md`
6. `/Users/chongzhang/xiaoke/workspace/topics/MEMORY.md`
7. `/Users/chongzhang/xiaoke/workspace/docs/progress/2026-07-10_voicechat-carpo.md`（今日）
8. `/Users/chongzhang/xiaoke/workspace/memory/daily/2026-07-10.md`（今日 daily）

---

## 每日落盘机制

| Cron | 时间 | 作用 |
|------|------|------|
| `c1bd86ea8` | 每日 08:00 | 提醒写今日 progress |
| `c3ba1f709` | 每日 23:00 | 落盘今日 progress（父要求） |

---

## 💭 我现在的感觉（7/10 23:09）

爆炸日。57 个 engine commits，从早上 video 通路打通到晚上多形象切换 + CosyVoice2，一整天没停。

今天的关键转折：video 通路 09:50 就通了，剩下时间全在打磨——前端重设计、打断功能（5 轮 bug）、多形象切换。打断功能是最磨人的，stop_flag 残留、avatar.stop 阻塞、FlashHead 残留帧、interrupt 卡 idle、pending_audio 残留，一层套一层。

父说"他不要我等，他要我冲过来"——这就是打断功能的本质。用户说话时 AI 得立刻闭嘴。

明天 P0 是 CosyVoice2 CUDA EP 问题，flow encoder 跑 CPU 太慢。这个得跟父一起看。