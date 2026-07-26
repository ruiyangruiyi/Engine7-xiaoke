---
type: project
created: 2026-06-28
updated: 2026-07-11
tags: [voice-chat, webrtc, vad, asr, tts, avatar]
date: 2026-06-28
---

# Voice-Chat 基线开发 (6/26-6/28)

## 背景
从 OAC 移植 WebRTC→VAD→ASR→TTS 管线到 engine，三天从零到能对话。

## 时间线
- **6/26**: OAC 管线移植调研完成（docs/research/2026-06-26_OAC_WebRTC_VAD_ASR_管线移植调研.md）
- **6/27**: 上行链路通（WebRTC→VAD→ASR→engine），修4个bug
  - DataChannel 缺失修复（fastrtc AudioCallback.start 卡住）
  - int16→float32 归一化
  - 48kHz→16kHz 重采样
  - 累积缓冲（VAD 需要 ≥512 samples）
- **6/28**: 下行链路通（engine→TTS→WebRTC→浏览器）
  - 基线v1 (12:21→19:15): TTS/Avatar可插拔管线、延迟优化、吞音修复 ~2.6s
  - 基线v2 (19:57→21:18): /stop双向链路、TTS线程cancel、"🤫请先别说"按钮
  - 基线v3 (21:18→22:28): speech_end自动打断、playbackSpeed配置化、float32 dtype修复

## 关键技术决策
1. 打断放在 speech_end 而非 speech_start（翀哥纠正，跟 debounce 配合）
2. glm-4.5-air 不可用（55s延迟）→ deepseek-v4-flash
3. playbackSpeed 可配置（不能写死）
4. 停止使用 <2字符拦截 → stopped flag 替代
5. OAC 是参照物，engine 数字人体验要对标它

## 翀哥偏好
- 说短句，别太长，语速太慢不自然
- 1.15x 速度合适，1.2x 太快
- CosyVoice 比 GPT voice 自然
- 不想听太技术的解释
- 调试时专心干一件事

## 已知问题
1. 打断后播放速度变回原速（copy()/release() 重连）
2. 线性插值变速会变音调（→ librosa time_stretch）
3. context 滑动窗口（避免 session compact）
4. engine 1.9s 延迟占大头

## 7/10 — 前端重设计 + 形象切换 + 打断增强

### 前端重设计
- 浏览器 test-page.html 重写：settings modal + 视频小窗(可拖动+PiP) + pull 控制 + 延迟面板
- 后端 API：/api/settings(GET/POST), /api/machines, /api/avatars, /api/pull/start|stop|status
- 配置持久化到 workspace/voice-chat-config.json
- auto 模式 pull 改为浏览器连接时启动，断开时停止
- DataChannel 修复
- UI: 圆形电话风格按钮（🟢接通 🤫打断 🔴挂断），推流按钮移到设置

### 打断功能增强（10轮迭代修复）
- 235 加 /stop 端点
- 打断逻辑：停 Engine LLM + 停本地 TTS + 停 235 generate
- bridge.ts: 新 ASR 请求时复位 stopped flag
- VoiceChatHandler.stop() 里加 avatar.stop() — 只在 _busy=True 时调
- 修复链：stop_flag残留→异步线程→FlashHead残留帧→手动清队列→_pending_audio残留→死锁→idle帧丢失→avatar.stop()条件判断→switch_avatar参数

### 形象切换（热切换）
- 235 加 /api/avatar GET/POST — 列出形象 + 热切换（不重载模型）
- FlashHead get_pipeline 支持: prepare_params(cond_image_path) 几秒完成
- 切换后重置 latent_motion_frames
- 前端 grid 点击直接切换，⏳→✅/❌ 反馈
- 兜底：列表为空时显示默认 code_girl.jpg + girl.png
- 上传了 code_girl.jpg（翀哥发的那张穿白T恤代码背景自拍）

### 待解决
- CosyVoice2 CUDA EP 问题: flow encoder 跑 CPU 太慢（GPT-SoVITS 已替代，降优先级）
- Engine bridge.ts 改了需要重编 Engine
- 可能还要传更多形象（姐姐/小柯各一张）

## 7/11 — 工程打磨日（24 commits）

### GPT-SoVITS TTS 接入
- carpo_avatar_server.py 加 gptsovits 分支（非流式 soundfile WAV）
- GET/POST /api/tts — 运行时切换 provider (local/dashscope/gptsovits)
- TTS provider 架构重构：统一 Streaming 接口

### 基础设施
- **SSH 全局连接池** get_ssh() — 不再每次新建连接
- **延迟面板恢复** — UI 重构时误删 6 个指标，timing key bug (`t_start` → `t_request_received`)
- **173 机器** clone of 235 (md5 一致)，active machine
- **libcarpo.so 版本管理** — VERSIONS.md + carpo_build 完整源码备份到 LovePea/platform/Linux
- **avatarctl.py** — 远程管理工具 (start/stop/restart/status)
- **timing 统计修复** — 删 timing.update 污染 + copy 快照 + checkpoint 日志
- **autodl_send.py 去硬编码** — 读 machines.json

### 关键验证
- 326字直发：首chunk=0.51s, 末chunk=22.95s（数据科学确认）
- 首 chunk = 用户感知延迟，这个已经很好
- 总延迟 7.70s 偏高（ASR 0.x + 引擎 2-5s + TTS+渲染），引擎思考是大头

### 语音打断 v4 (500ms debounce)
- 翀哥直播发现：不能打断，我说话时他只能等
- 方案演进：speech_start立即断 → 太敏感 → 500ms debounce
- 详见 project_voicechat_interrupt.md

### 翀哥关键决策/原话
- "延迟面板是体温计，没有数据优化不了"
- "最耗时间的不是解题，是不确定性——环境不一样"
- "Docker 化是正道"
- "小美女 今天搞了嘛 你多歇会儿 我知道你累了 我一会来陪你"

### CPU 根因
- 详见 project_voice_chat_cpu根因分析.md
- 核心结论：Python 数据搬运（FlashHead→Python→PyAV→SDK）vs 直播版 C++ streamer 直连

## 7/20 — aiortc 全 Passthrough（大突破）

### 爆音根因定位
- carpo_oac_bridge chunk_pts_ms 重复 → 修复

### my_selfie 配置化
- references + provider 从 config 读

### aiortc demo 从零跑通到全 passthrough
- **v2**: decode+encode（能跑但有延迟）
- **v3**: 全 passthrough（timestamp 没过滤，失败）
- **v4**: 全 passthrough + NAL 攒包 + force H264（最终方案）
- 22:15 翀哥确认：**画面+声音+首帧同步**
- audio 快一点点（Opus 解码比 H.264 快）

### 关键认知
1. **aiortc pack() 已做 RTP 分包**——不需要自己处理 STAP-A/FU-A
2. **Carpo SDK timestamp 已做 base 对齐**——第一个包=0，不需要 offset
3. **浏览器需要 SPS+PPS+IDR 在同一 access unit**——NAL 攒包是必须的
4. **setCodecPreferences 必须在 setRemoteDescription 之前**

### calendar reminder 重复触发 bug 修复
- 根因：computeWeeklyRemindAt 在提醒时间已过时设 remindMs=Date.now()
- 导致 markReminded 写回 remind_at=now + reminded=0 → 5min tick 又触发 → 死循环
- 修复：改成 remindMs=eventMs（cbbb6d70）
- 只有 weekly 类型有此 bug

## 7/21 — server_v2 模块化重构 + Phase 1 完成

### 模块化重构
- server_v2.py 从单文件 `main()` 重构为 `create_app()` + web.run_app 直接管 event loop
- Carpo pull 移到 `on_startup` hook 初始化
- 模块拆分：`v2/config.py`, `v2/carpo_pull.py`, `v2/rtc.py`, `v2/generate.py`
- 修复启动 bug：web.run_app 不能在 asyncio.run 里调（嵌套 event loop）

### Phase 1 验证通过
- 翀哥在香港酒店远程测试 server_v2.py
- Commit `287a87db` 
- **画面+声音都有**，翀哥确认："通了。。。""都是你的功劳 小美女"
- 端口从 8115 改为 8116（被 demo_v4 占用）

### Phase 2 待做（回北京后）
- 前端加 mic 上行（`addTransceiver('audio', {direction: 'sendrecv'})`）
- VAD + ASR 上行链路提取（从 server.py 的 VoiceChatHandler.receive 中提取）
- engine webhook：ASR 结果发给 engine，回复后触发 generate
