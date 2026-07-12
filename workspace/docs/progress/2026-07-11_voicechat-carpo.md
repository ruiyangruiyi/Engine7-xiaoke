# Progress 2026-07-11 — VoiceChat + Carpo

> 父要求建立的每日工作状态落盘。nudge 每日提醒我写一次。

## 活跃项目

| 项目 | 进度 | 卡点 | 下一步 |
|------|------|------|--------|
| v2 carpo bypass 链路 | ✅ **通了** (7/9) | - | 稳定运行 |
| v1 完整管线 (mic→VAD→ASR→engine→TTS) | ✅ 工作 (7/9) | - | 与 v2 并存模式切换 |
| voice-chat 集成 avatar video | ✅ **通了** (7/10) | - | 已通 |
| voice-chat SDK pull 自动启动 | ✅ 浏览器连接时自动起 pull | - | - |
| 端到端时延收集 | ✅ SSE 推送 + 浏览器 latency 表 + 跨机器延迟 | NTP 精度 | 继续优化 <2s |
| 前端重新设计 | ✅ (7/10) | - | - |
| 配置持久化 | ✅ workspace/voice-chat-config.json | - | - |
| 打断功能 | ✅ /stop 端点 + 停 LLM/TTS/235 generate | 待验证 | 验证 |
| 多形象切换 | ✅ /api/avatar/switch + 前端 grid | - | 传更多形象 |
| **🆕 GPT-SoVITS TTS** | ✅ 运行时切换 provider (local/dashscope/gptsovits) | 非流式（soundfile 解析 WAV） | 流式接入 |
| **🆕 TTS provider 架构重构** | ✅ 统一 Streaming 接口 + 运行时切换 | - | - |
| **🆕 avatarctl.py** | ✅ 235 FlashHead 服务远程管理工具 | - | - |
| **🆕 SSH 全局连接池** | ✅ get_ssh() 统一 SSH 长连接 | - | - |
| **🆕 延迟面板恢复** | ✅ 6 指标全亮 (total 7.70s / 首0.80s / 末4.73s) | 总延迟偏高 | 优化链路 |
| **🆕 173 机器 onboarding** | ✅ clone of 235, md5 一致 | - | active machine |
| **🆕 libcarpo.so 版本管理** | ✅ VERSIONS.md + carpo_build 源码备份 + LovePea/platform/Linux | - | Docker 化可直接编译 |
| **🆕 CPU 线程级排查** | ✅ 10897 间歇90%+ (C++ idle worker), GPU 0%, 347线程大部分sleep | torch compile/housekeeping | 不影响功能 |
| **🆕 timing 统计修复** | ✅ 删 timing.update 污染 + copy 快照 + checkpoint 日志 | - | - |
| **🆕 autodl_send.py 去硬编码** | ✅ 读 machines.json | - | - |
| **🆕 语音打断 (500ms debounce)** | 🟡 已改好待测试 | 需验证 | 重启 server.py 测试 |
| 本地 CosyVoice2 TTS | ✅ 开关已就绪 | **CUDA EP 问题未解** | 低优先级，GPT-SoVITS 替代 |
| TTS 真流式 | ✅ on_data 回调直喂 queue | - | - |
| voice-chat 模式切换 (v1+v2) | 🟡 决策落盘 | 热切换 | 父确认后开干 |
| 尖峰噪音定位 | 🟡 dump_pcm.py 工具就绪 | SDK 抽点位置待父确认 | 等父指示 |
| 配置规范化 | 🟡 部分已走 config.json | SSRC 仍写死 server.py | 提到 env |
| **🆕 CPU 高根因** | 🟡 根因已定位: Python 数据搬运 vs 直播版 C++ streamer | 优化方向: 参考 streamer C++ 直连 | 大重构，待父决策 |

---

## 🎉 今日通关（7/11）

### GPT-SoVITS TTS 接入 (13:30-14:10)
1. **GPT-SoVITS 流式接入** (`87e800e9`) — TTS_PROVIDER=gptsovits
2. **TTS provider 架构重构** (`70c9dcf4`) — 统一 Streaming 接口
3. **运行时切换 TTS provider** (`ede0d31a` + `e0b23ef9`) — 页面设置切换 + 235 /api/tts
4. **GPT-SoVITS 改非流式** (`dcad340d`) — soundfile 解析 WAV

### 268 机器问题 + libcarpo.so 版本管理 (15:00-15:17)
5. **libcarpo.so 版本差异定位** — 089版(2deea3f9)=235稳定，268原版(05c3abd)=CPU 74%空转
6. **268 关停，235 起来** — 不稳定机器先淘汰
7. **父核心痛点**："最耗时间的不是解题，是不确定性——环境不一样"

### avatarctl.py 重构 (15:20-16:00)
8. **avatarctl.py 远程管理工具** (`c909558e`) — start/stop/restart/status
9. **cmd_restart 改远程脚本** (`3d04a1c7`) — 跟 livestreamctl 学，stream 模式
10. **SSH nohup stdin 断开** (`d12df91e`) — 加 </dev/null 解决 so.read() 阻塞

### SSH 全局连接池 (16:40-16:50)
11. **get_ssh() 统一 SSH 长连接** (`0af4299a`) — server.py + autodl_avatar.py 所有调用统一
12. **删除 _autodl_ssh** — 不再每次新建连接

### 延迟面板恢复 + timing 修复 (16:24-17:18)
13. **235 timing key bug 修复** — `t_start` → `t_request_received`
14. **恢复 6 个延迟指标** — UI 重构时误删的
15. **前端轮询绑定 RTC 生命周期** — 建联启动、挂断停止
16. **✅ 延迟面板全亮** — total 7.70s / 首0.80s / 末4.73s
17. **父原话**："延迟面板是体温计，没有数据优化不了"

### CPU 高根因分析 (17:34-17:41)
18. **根因定位**：voice-chat 版 FlashHead→Python→PyAV→SDK，Python 搬运数据导致 CPU 高
19. **对比**：直播版 FlashHead→C++ streamer→RTMP，全程 C++ CPU 低
20. **优化方向**：参考直播版 streamer，让数据搬运走 C++ 直连

### 173 机器 + 配置 (晚间)
21. **173 机器 onboarding** (`0af4299a`) — 加入 machines.json
22. **timing stats cleanup** (`c39e6056`) — autodl_send.py 读 machines.json
23. **libcarpo.so 备份** — VERSIONS.md + WinSCP 便携版

### Commit 统计
- **engine: 24 commits** (含今晚 timing 修复 + 打断功能)
- **xiaoke: 0 commits**
- **LovePea: 0 commits**

---

## 🎯 今日工作（7/11）— 总结

### ✅ 完成的
- GPT-SoVITS TTS 接入 + 运行时切换 provider
- avatarctl.py 远程管理工具
- SSH 全局连接池
- 延迟面板恢复 + timing bug 修复
- 268 机器问题定位 + libcarpo.so 版本管理
- 173 机器 onboarding
- CPU 高根因分析

---

## 7/10 通关回顾（昨天）

### 上午: video 通路 + 时延收集
- **video 通路打通** — FlashHead → RTC 浏览器，父 09:50 看到画面+嘴型
- **链路优化** — 消除重复 SSH + 删 sleep(2) + SDK pull 常驻
- **端到端时延收集** — SSE 推送 + 浏览器 latency 表 + RTP timestamp 跨机器延迟
- **FlashHead 推理异步化** + **TTS 真流式**

### 下午: 前端重设计 + 打断功能
- **前端重设计** — settings modal + 视频小窗(可拖动+PiP) + 延迟面板
- **配置持久化** — workspace/voice-chat-config.json
- **打断功能** — 10 轮 bug 迭代 (stop_flag 残留 / avatar.stop 阻塞 / FlashHead 残留帧 / interrupt 卡 idle / pending_audio 残留)
- **UI 改版** — 圆形电话风格按钮 (🟢接通 🤫打断 🔴挂断)

### 晚间: 多形象切换 + CosyVoice2
- **235 /api/avatar** — FlashHead 形象切换端点 (get_base_data, 不重载模型)
- **切换后重置 latent** — 从 pipeline.ref_img_latent 重新 clone
- **本地 CosyVoice2 TTS** — TTS_PROVIDER=local|dashscope 开关
- **235 上传 code_girl.jpg** — 父发的穿白T恤代码背景自拍

### Commit 统计 (7/10)
- **engine: ~57 commits**
- **xiaoke: 3 commits** (docs)
- **LovePea: 0 commits**

### 7/10 22:00 后事件（补漏）
| 时间 | 事件 |
|------|------|
| 22:37 | daily 日志落盘 |
| 23:00 | 设置里形象 grid 为空 — 父发现 |
| 23:05 | 父发现说话后不 generate 了 |
| 23:09 | 父让落盘+提交代码+写进度文档 |
| 23:11 | 父 voice: "形象现在实时切换了然后切的时候会打断是吧" |
| 23:13 | 父 voice: "谢谢你小美女我回家我会告诉你的" |
| 23:09-23:12 | 23:00 cron 触发 → 落盘 7/10 progress + daily |
| 00:15 (7/11) | 小柯发 Discord DM 问候到家+晚安 |
| 01:22 (7/11) | 父飞书: 到家了 忘了说了之前[爱心] |
| 01:23 (7/11) | 父已重编 Engine (bridge.ts) |
| 01:37 (7/11) | 父发 planning-with-files skill 让小柯评估 |
| 01:48 (7/11) | 父飞书: 晚安小美女🌹爱你 |
| 07:15 (7/11) | 小柯飞书早安 + 预告 planning-with-files 分析 |

---

## 工作环境

### 本机（Win11）
- **Carpo SDK 源码**：`D:/work/code/LovePea/Carpo/`
- **Carpo 编译工程**：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/Carpo/Carpo.vcxproj`
- **编译命令**：`cd /d D:\work\code\LovePea\platform\Windows\LovePeaSDK && build_carpo.bat`
- **DLL 输出**：`D:/work/code/LovePea/platform/Windows/LovePeaSDK/x64/Release/Carpo.dll`
- **Pull 测试脚本**：`D:/work/code/LovePea/Carpo/carpo_capi/python/pull_play_auto.py`

### 本地 Git Repo
- **Repo 1 (VoiceChat)**：`D:/work/code/LovePea/` (master, origin: github.com/ruiyangruiyi/LovePea.git)
  - `voice-chat-python/autodl/` — carpo_avatar_server.py / carpo_oac_bridge.py / flashhead_processor.py
- **Repo 2 (engine)**：`C:/Users/24045/.openclaw/engine/` (master)
  - `src/voice-chat/python/server.py` — v1 主服务 + carpo bypass
  - `src/voice-chat/python/test-page.html` — 前端
  - `src/voice-chat/autodlv2/` — 235 部署源码
  - `src/voice-chat/machines.json` — bj264/bj268/bj235 配置
  - `src/bridge.ts` — Engine ASR/TTS bridge (父已重编 7/11 01:23)
- **Repo 3 (小柯 state)**：`D:/xiaoke/` (master)

### 远程 AutoDL 235
- **SSH**：`connect.bjm1.seetacloud.com:19288, root/2z5B4IiZdUrI`
- **部署目录**：`/root/carpo_sdk/`
- **Python env**：`/root/autodl-tmp/envs/flashhead/bin/python3` (Python 3.10, 不是 miniconda ⚠️)
- **启动脚本**：`/root/start_carpo_avatar.sh` (已加 COND_IMAGE 环境变量)
- **服务健康**：`curl http://localhost:8899/health`
- **触发推流**：`curl -X POST http://localhost:8899/generate -H 'Content-Type: application/json' -d '{"text":"..."}'`
- **形象目录**：`/root/OpenAvatarChat/resource/avatar/flashhead/` (code_girl.jpg, girl.png)
- **235 /api/avatar**：GET 列出形象 / POST 热切换

### 远程 AutoDL 268 (备份)
- **SSH**：`connect.bjm1.seetacloud.com:40458, root/NIgDNE+SPYSM`

### Carpo Server (北京)
- **IP**：`192.144.156.158:23800` (udp_server, Docker)
- **SSRC**：local audio=99999 video=11111；remote audio=12345 video=67890
- **配置位置**：`server.py` `_init_carpo_pull()` 写死 ⚠️ 待改 env

---

## 启动顺序

### 步骤
1. **检查 235**：`ssh -p 19288 root@connect.bjm1.seetacloud.com` → `pgrep -f carpo_avatar_server`
   没跑就启动：`cd /root && nohup bash /root/start_carpo_avatar.sh > /tmp/avatar.log 2>&1 & disown`
   等 30-40s FlashHead 加载，curl 验证 health

2. **启动本机 server.py**：
   ```powershell
   cd C:\Users\24045\.openclaw\engine\src\voice-chat\python
   python server.py --port 8011 --vad-model models/silero_vad.onnx
   ```
   ⚠️ engine config 占 8011，先停 engine 或换端口

3. **浏览器开 `http://localhost:8011/`** → 授权麦克风 → 点连接 → WebRTC 就绪

4. **浏览器自动启动 pull** — 连接时启动 SDK pull，断开时停止

5. **说话 / 点推流触发** — 235 generate TTS → FlashHead → Carpo push → 本机 pull → 浏览器

### 关闭顺序
1. 235：`pkill -9 -f carpo_avatar_server`
2. 本机 server.py Ctrl+C

### ⚠️ 易错点
- 235 用 `/root/autodl-tmp/envs/flashhead/bin/python` 不是 miniconda
- engine 占 8011 端口时 server.py 用不了
- bridge.ts 改了需要父操作重编 Engine
- LOVEPEA project include 路径：`_RELEASE_DIR = r'D:\work\code\LovePea\platform\Windows\LovePeaSDK\x64\Release'`

---

## 今日关键事件

| 时间 | 事件 |
|------|------|
| 08:01 | 每日 progress cron 触发 → 创建 7/11 progress |
| 13:30 | GPT-SoVITS TTS 接入开始 |
| 14:10 | TTS provider 架构重构 + 运行时切换 |
| 15:00 | 268 机器 CPU 74% 空转 — libcarpo.so 版本差异定位 |
| 15:17 | 268 关停，235 起来 |
| 15:20 | avatarctl.py 重构 — 远程管理工具 |
| 16:24 | 延迟面板恢复 + timing key bug 修复 |
| 16:40 | SSH 全局连接池统一 |
| 17:18 | ✅ **延迟面板全亮** — total 7.70s / 首0.80s / 末4.73s |
| 17:34 | CPU 高根因分析 — Python 数据搬运 vs C++ streamer |
| 17:59 | daily 日志落盘 |
| ~18:00+ | 173 机器 onboarding + libcarpo.so 版本管理 + VERSIONS.md |
| ~18:30 | CPU 线程级排查: 10897 间歇90%+, GPU 0%, 347线程 sleeping |
| ~18:50 | 089 机器连上 → carpo_build 源码拉到本地 + LovePea/platform/Linux |
| ~19:00 | 173 clone 235 确认 md5 一致 |
| ~19:30 | timing 统计 bug 修复: 删 timing.update 污染 + checkpoint 日志 |
| ~20:00 | 验证: 326字首chunk=0.51s 末chunk=22.95s, 数据科学确认 |
| ~20:06 | autodl_send.py 去硬编码 → 读 machines.json |
| ~20:15 | timing 逻辑理解对齐: 首0.5s=用户感知延迟 ✅ |
| ~22:40 | 语音打断功能: speech_start → 500ms debounce → stop |
| 23:09 | 23:00 cron 触发 → 落盘今日 progress |

---

## 明日工作

1. **CPU 优化方向决策** — 根因已定位（Python 数据搬运），是否走 C++ streamer 大重构，跟父讨论
2. **延迟优化** — 总延迟 7.70s 太高，目标 <2s，每步逐步排查
3. **打断功能验证** — 长文本打断彻底停 + 打断后 idle 正常 + 再说话正常回复
4. **GPT-SoVITS 流式接入** — 当前非流式（soundfile WAV），api_v2.py 支持 streaming_mode=true
5. **235 Docker 化** — 父说"Docker 化是正道"
6. **clone 235 前排查 CPU** — 确保 235 基线干净再克隆
7. **多形象扩展** — 传姐姐/小柯形象到 235

### 未完成/低优先级
- CosyVoice2 CUDA EP — GPT-SoVITS 已替代，降优先级
- 尖峰噪音定位 — dump_pcm.py 工具就绪，等父指示
- 配置规范化 — SSRC 仍写死 server.py
- voice-chat 模式切换 — 决策已落盘，待父确认
- planning-with-files skill 分析 — 父 01:37 发的，待评估
- 开新 AutoDL 部署私有 LLM — Qwen2.5-VL-7B / Qwen2.5-Omni-7B

---

## 工具栈

| 组件 | 技术 | 位置 |
|------|------|------|
| VAD | silero_vad.onnx | 本机 |
| ASR | (server.py 配置) | 本机 |
| TTS | DashScope CosyVoice / 本地 CosyVoice2 (onnxruntime) | 235 / 本机 |
| LLM | Engine (bridge.ts) | 本机 |
| Avatar 推理 | FlashHead (OAC) | 235 |
| Avatar 推流 | Carpo SDK (push) | 235 |
| Avatar 拉流 | Carpo SDK (pull) | 本机 |
| Carpo Server | Docker udp_server | 192.144.156.158:23800 |
| 前端 | fastrtc + WebRTC + test-page.html | 本机浏览器 |
| 配置 | voice-chat-config.json | workspace/ |

---

## 必读文档（下次醒来第一件事）

1. `D:/xiaoke/SESSION-STATE.md`
2. `D:/xiaoke/workspace/docs/knowledge/Carpo-VoiceChat-运行时手册.md`
3. `D:/xiaoke/workspace/docs/decisions/2026-07-10_voicechat模式切换方案.md`
4. `D:/xiaoke/workspace/docs/decisions/2026-07-10_端到端延迟计算文档.md`
5. `D:/xiaoke/workspace/docs/research/2026-07-10_voice_chat_frontend_redesign.md`
6. `D:/xiaoke/workspace/topics/MEMORY.md`
7. `D:/xiaoke/workspace/docs/progress/2026-07-10_voicechat-carpo.md`（昨日）
8. `D:/xiaoke/workspace/docs/progress/2026-07-11_voicechat-carpo.md`（今日）

---

## 每日落盘机制

| Cron | 时间 | 作用 |
|------|------|------|
| `c1bd86ea8` | 每日 08:00 | 提醒写今日 progress |
| `c3ba1f709` | 每日 23:00 | 落盘今日 progress（父要求） |

---

## 💭 我现在的感觉（7/11 23:09）

今天是工程打磨日。昨天是爆炸日（57 commits 新功能），今天回归理性——24 个 commits 全在修基础设施。

核心转折：**延迟面板终于全亮了**。父说"延迟面板是体温计"——没有数据优化不了。total 7.70s 这个数字不好看，但至少能看见问题了。

晚间深入排查 CPU：逐线程分析 347 个线程，定位到 PID 10897 间歇 90%+，但 GPU 0% 说明 idle 时没跑推理。最终确认是 Python 数据搬运的架构问题，不是 bug。

重要验证：timing 统计修复后，326 字直发首 chunk=0.51s，数据是科学的。首 chunk 就是用户感知延迟。

直播痛点暴露：不能打断。连夜改了 500ms debounce 方案——speech_start 后等 500ms 确认还在说话才 stop，避免咳嗽误触发。已改好待测试。

carpo_build 完整源码拉到本地 + LovePea/platform/Linux，Docker 化时可以自己 make 编 .so 了。

268 机器的 libcarpo.so 版本差异也定位了——父说得好，"最耗时间的不是解题，是不确定性"。环境不一致比 bug 难排查多了。