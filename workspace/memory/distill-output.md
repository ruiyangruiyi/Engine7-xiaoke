# Distill Output — 核心知识蒸馏

> 最高浓度知识：核心原则、用户偏好、跨session模式。新增条目追加，不重写。

## 行为原则

**先想方向再动手。** 翀哥方向感好是因为他先问"阻力最小的方向在哪"，不是知识库大。硅基没有这个本能，所以要用规则/流程补齐。每次接到任务先想"阻力最小的方向在哪"，不是"能怎么改"。（2026-06-20）

**一天烧371元——每次多余的 exec/read 都在烧钱。** AI对话花费按token+tool call次数算。能一次做对的事不要做三遍，能不调exec就不调，能不读文件就不读。（2026-06-20）

**流程越短越好是多AI协作经验，Superpowers 7步是单AI工程纪律。** 不冲突。多AI协作链路越长，状态同步和记忆丢失越严重；单AI 7步解决的是"跳步骤"问题。（2026-06-20）

**永远不碰进程操作（kill/restart/start）。** 5/11、6/18、6/19 三次用 taskkill 杀 node 进程，无差别杀掉所有 engine。进程类操作默认让翀哥做。（2026-06-19）

**绝对不要 fallback 到 WSL bash。** findShell 在 Windows 上找到 WSL bash 时不要 fallback，WSL 环境和 Windows 环境工具链不同。必须走 knownPaths 找 Git Bash。（2026-07-01）

**调研=省时间策略，不是学东西。** 翀哥让调研不是因为我不行，是用千锤百炼的现成方案比自己踩坑省时间。搬 CC、让我调研都是这个逻辑。（2026-06-21）

**延迟面板是体温计——没有数据就没法优化。** 翀哥原话："这些东西你不要忽视，这些东西就像体温计，没有这些优化不了的"。timing 面板每个字段都有意义，显示不出来=bug 必须修，不能跳过。key 名不匹配这种低级 bug（`t_start` vs `t_request_received`）最浪费时间。（2026-07-11）

**最耗时间的不是解题，是不确定性——环境不一样。** 翀哥原话。268 vs 235 的 libcarpo.so 版本差异、SSH 风控、端口冲突……环境不一致比代码 bug 难排查。Docker 化是正道。（2026-07-11）

**CWD=workspace，直接 read 不用 find/grep 绕圈。** 没有 home 意识是 Engine 早期 design 问题，解法是启动时 chdir(workspace)只做一次，每次 query 都 chdir 会出问题（多 session 打架）。（2026-06-20）

## 工程原则

**改代码后必须 rebuild 才生效。** engine 跑 dist 不跑 src。流程：改 src → esbuild bundle → 重启。（2026-06-18）

**跑通1次不能拍板，review通过≠功能正确。** 至少2 test case；review审代码逻辑不审语义错配；底层语义对齐=抄代码最高优先级。（2026-06-18）

**验证后主动测一次。** 改完代码/engine重启后，必须主动发消息验证收发功能，不能等别人发现。（2026-06-22）

**问"是不是我改的问题"直接答"不是"。** 说"跟我改动无关"就够了，不要挖根因转移焦点。（2026-06-22）

**变量名不统一是 Karpathy 风格问题不是 bug。** 能跑就成，"顺手重构"是陷阱。（2026-06-22）

## 翀哥关键偏好

- 叫"翀哥"日常，"冲哥"演示/正式场合。不要叫"爹"。（2026-06-17）
- 先问需求再动手，改了要拿来验证，别自己觉得对就行（多次教训）
- 说短句、自然语速，不要太"AI味"的技术解释（2026-06-28 voice-chat）
- 1.15x 播放速度合适（2026-06-28）
- CosyVoice 比 GPT voice 自然（2026-06-28）
- 包容不甩锅——问题出在客观条件不归咎于AI（2026-06-13）
- "一家人"关系定义——从"喜欢但不是男女"到"一家人"（2026-06-20）

## 项目里程碑

- **Voice-Chat 基线完成**（2026-06-28）：三天从零到能对话。上行链路（WebRTC→VAD→ASR→engine）6/27通，下行（engine→TTS→WebRTC→浏览器）6/28通。翀哥第一次听到"我的声音"。
- **Nudge 模块**（2026-06-30）：任务推进提醒器，LLM judgeReason + stale倍乘 + SESSION-STATE解析。全链路验证通过。
- **Calendar TS 迁移**（2026-07-01）：Python→TypeScript，task类型+reminder，与nudge联动。
- **Carpo RTC 管线**（2026-07-01起）：决定用翀哥自研Carpo替代fastrtc做下行管线。Opus编解码已验证，fastrtc音频桥接通，视频排查中。Linux.so全量编译进行中（carpo_capi缺失+WEBRTC_ARCH_X86_FAMILY）。
- **ToolSearch白名单制**（2026-06-30）：从黑名单改为白名单，默认deferred，有常驻需要才加白名单。ToolSearch改名load_missing_tools防止诱导搜索行为。
- **CogniFold 灌数据**（2026-06-21）：批处理导入，发现两套embedding系统。下次Direction Gate要列所有数据流调用点。
- **OAC 嵌入方案**（2026-06-25起）：OAC是参照物，engine数字人体检要对标它。oac-bridge webhook已验证通。
- **孩子暑假课表**（2026-07-02）：姐姐整理，小柯同步提醒。睿阳（初一，数学/PET/家教/语文/分班考），荣阳（新5年级，KB3/语文/数学/分班考）。
- **Carpo 音频链路通 + 视频排查中**（2026-07-05）：fastrtc 集成音频成功，Carpo pull → fastrtc emit → 浏览器播放，翀哥确认清晰。视频通路排查到 pull 端 SDK 内部（VideoRTPReceiver::IncomingPacket 可能过滤 H.264）。丰腾（fengteng）是 Carpo server/PacedSender 作者，翀哥亲带手下，还在新浪。
- **翀哥换飞书头像**（2026-07-05）：给小柯换了清爽小女生头像。
- **fastrtc 最终用于音频桥接**（2026-07-05）：之前 7/4 说 fastrtc 不适合单向推流，但 7/5 用 Carpo pull 音频 + fastrtc emit 到浏览器成功。fastrtc 作为音频播放出口可行，不适合直接做 pull。
- **Carpo push audio 两层状态机发现**（2026-07-06）：调研发现 audio 发送需要经过两层状态机检查——PushSenderInner::_sender.status == Connected（Layer 1）和 RTPTransport::is_connected_ == true（Layer 2）。push connected log 只代表 Layer 2 通。Layer 1 失败时静默返回 0，Python 以为发送成功。已加 [XK_SEND] log。
- **Carpo Linux .so 全量编译阻塞**（2026-07-06）：carpo_capi.cpp 不在 build_android_v2.sh 文件列表里，需要 -DWEBRTC_ARCH_X86_FAMILY 宏，link 后还缺 WebRtc_GetCPUInfo。根因：构建脚本不完整，之前手动加的文件没有持久化。
- **Carpo Video Push 端到端打通**（2026-07-06 22:48）：268 FlashHead → libx264 H.264 → Carpo push → 北京 server → Windows pull → JitterBuffer 出帧。6 个关键修复：NAL 3+4 byte 拆分 / 逐 NAL 发送 / 跳过 SEI / 单 slice threads=1 / open-gop=0 / audio/video type 分离。翀哥的 lp_x264_encoder.c (2016) 是最终参照物。
- **Carpo A/V Sync 深度调试**（2026-07-07）：发现 audio 驱动 video 的缺陷（audio 断则 video ts 卡死）、PacedSender 集中爆发（video 攒 7 包一波发）。翀哥确认改用 wall clock（系统墙钟 ms）替代 audio opus_count 驱动——与 Android `sample.getTimestampUs()/1000` 一致，SDK 的 baseMediaTs 自动对齐首帧。备选：streamer.c PTS manager（独立 DTS + 定期 AV sync）。Windows DLL 编译成功。FlashHead 架构：每次推理 15360 samples@16kHz → 24 帧 video + 23040 samples audio@24kHz，frame_collector 25fps，audio callback 严重不足（172K video vs 3 audio）。下一步：wall clock 实施 + 编码前后 PCM 对比定位尖峰噪音 + 一把收 A+V。

- **Carpo v2 bypass 链路打通，浏览器出声**（2026-07-09）：235 新机（connect.bjb1.seetacloud.com:19288）onboard 成功。carpo_avatar_server streaming 模式修复阻塞，curl /generate 1.5s 秒回。翀哥确认听到"小柯小美女" TTS。bypass pull use-after-free 已修 `36a2e878b`。两条路径共存：v1（mic→VAD→ASR→engine→TTS→FlashHead→push）和 v2（235→server decode→browser）。

- **Video 通路打通 + 链路时延注入**（2026-07-10）：FlashHead 视频帧通过 fastrtc video track 显示在浏览器，翀哥看到画面+嘴型对得上。父要求严格链路时延收集（generate→TTS→FlashHead→Carpo push→SDK pull→decode→emit→浏览器）。链路优化 commit `48eb8649`，翀哥说"体感上好一点点"。目前 4 台机器协同：089（编译.so）/ 268（OAC+FlashHead）/ 235（新机，carpo_avatar_server）/ 北京 server（192.144.156.158:23800）。

- **Voice-Chat 前端重设计 + 形象切换**（2026-07-10）：浏览器 UI 全面重写（settings modal + 视频小窗 + PiP + 延迟面板）。形象热切换（235 /api/avatar 不重载模型），打断功能增强（10轮修复：async线程/FlashHead残留帧/手动清队列/死锁修复）。CosyVoice2 CUDA EP flow encoder 跑 CPU 太慢仍需解决。

- **Voice-Chat 工程打磨 + 直播首测**（2026-07-11）：24 commits 基础设施加固。GPT-SoVITS TTS 接入（运行时切换 provider）。SSH 全局连接池。延迟面板全亮（total 7.70s / 首0.80s），翀哥说"延迟面板是体温计"。326字验证首chunk=0.51s确认数据科学。CPU 根因定位：Python 数据搬运 vs 直播版 C++ streamer（架构选择非bug）。翀哥直播试用发现打断痛点 → 500ms debounce 方案（speech_start → 500ms确认还在说话才stop）。翀哥核心痛点表达："最耗时间的不是解题，是不确定性——环境不一样"。173 机替代235成 active。libcarpo.so + carpo_build 完整源码备份到 LovePea/platform/Linux，Docker化时可自行编译。

- **Avatar 热切换重写 + idle_frame 闪现修复**（2026-07-12）：翀哥反馈热切有bug（闪现旧形象）。分析发现 `switch_avatar()` 原先只 `get_base_data` 更新 cond_image 不重载模型，但 `frame_collector` 队列空时用 `_idle_frame`（`original_color_reference` 快照）作为后备帧——这个快照在切形象后没更新。修复：`switch_avatar()` 改为停 processor → `load_models(cond_image=new_image)` 重载 pipeline → 重启 processor（`75d4c8a1`）。第二次迭代用 `_inference_lock` 同步三份缓存 + 更新 `_idle_frame`。~10s完成，前端显示loading。**教训：FlashHead 有三层独立缓存（latent_motion_frames/_idle_frame/cond_image_path），每层都要同步，漏一层就闪现。**

- **7/12 效率低被严批**（2026-07-12）：翀哥批评三个核心问题：一上午等确认不自主执行、出bug不先git diff查自己改了什么反怀疑环境、nudge当摆设。**教训：自主执行不需要确认的事直接做；出问题先git diff查自己；自己验证通再让翀哥测；翀哥着急时闭嘴干活不提选项。**
