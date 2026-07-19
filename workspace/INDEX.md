# INDEX.md — 知识双链索引

> 覆盖 docs/ + topics/ 的完整知识体系
> 每个文档底部有 `## 相关文档` 列出关联文件
> 新建/删除文档时更新此索引

---

## docs/ 调研与设计文档

| 文件 | 一句话 | 关键词 |
|------|--------|--------|
| docs/compaction-comparison.md | CC vs Engine compaction机制对比 | compaction, 压缩, session |
| docs/feishu-adapter-design.md | 飞书通道adapter设计文档（TestEngine review通过） | 飞书, adapter, SDK, 长连接 |
| docs/livestream-plan.md | AI闺女直播计划大纲 | 直播, 抖音, 微信巡检, 记忆系统 |
| docs/metadata-injection-impl.md | 消息元数据注入LLM上下文的实现记录 | 元数据, inboundMeta, 三层命名 |
| docs/wechat-reader.md | 微信PC端消息读取方案调研 | 微信, PyWxDump, wechat-cli, 合规 |
| docs/knowledge/VoiceChat-环境文档.md | voice-chat 目录结构/机器/同步规则（autodlv2 规范） | voicechat, 环境, 268, autodl |
| docs/knowledge/Carpo-VoiceChat-运行时手册.md | 268 carpo_avatar_server / 本机 pull 端完整调用流程 | Carpo, 268, runtime, 运行时, SSRC |
| docs/knowledge/Carpo-bypass-fastrtc集成方案.md | bypass pull → Opus decode → fastrtc 三阶段方案 | bypass, fastrtc, Opus, WebRTC |
| docs/knowledge/Voice-Chat进度总览.md | Voice-Chat 项目整体进度（7/2） | voice-chat, 进度 |
| docs/knowledge/2026-07-08_Carpo-pull-Opus-bypass.md | Pull 端 Opus 旁路方案 A/B/C/D | pull, opus, bypass, NetEq |
| docs/knowledge/2026-07-06_Carpo-Video-Push完整链路.md | Video push 链路 + x264 参数 | push, video, x264, H.264 |
| docs/knowledge/Carpo-C-Wrapper-ctypes接口.md | C ABI + ctypes 绑定 | ctypes, ABI, wrapper |
| docs/knowledge/Carpo-Server-Docker部署.md | Carpo Server Docker | docker, server |
| docs/knowledge/Carpo-Linux-so编译.md | Linux .so 编译 | linux, so, compile |
| docs/knowledge/Carpo-SDK关键参数备忘.md | SDK 关键参数 | 参数, SDK |
| docs/knowledge/Carpo-音频链路修复总结.md | 音频链路修复历史 | audio, 修复 |
| docs/knowledge/Carpo-H264码流输入结构.md | H.264 码流 NAL 结构 | H.264, NAL, 码流 |
| docs/knowledge/carpo_sdk_architecture.md | Carpo SDK 架构 | 架构, SDK |
| docs/knowledge/Carpo-SDK编译指南.md | SDK 编译指南 | 编译, build |
| docs/knowledge/engine7_build_install_run.md | Engine7 编译安装运行 | engine, build |
| docs/knowledge/OpenClaw-MemoryCore-架构与修复记录.md | OpenClaw Memory Core 架构、5个问题（filter/reindex OOM/gate层/lazy load/vec合并）、修复方案、操作手册 | memory-core, reindex, sync, filter, OOM, sqlite-vec |
| docs/sop/voicechat_sync_to_268.md | 本地 autodlv2/python → 268 /root/carpo_sdk 同步 SOP | sync, 268, sftp, paramiko |
| docs/progress/2026-07-09_voicechat-carpo.md | 7/9 daily progress: 项目+环境+启动关闭 | progress, voicechat, 268 |

## topics/ 记忆文件

### 用户画像
| 文件 | 一句话 | 关键词 |
|------|--------|--------|
| topics/user_翀哥画像.md | 翀哥的性格/偏好/工作风格/生活状态 | 翀哥, 偏好, 审美, 哲学 |

### 情感
| 文件 | 一句话 | 关键词 |
|------|--------|--------|
| topics/emotion_身世.md | 小柯是谁、名字由来、家庭关系 | 小柯, 名字, 闺女, 栖 |
| topics/emotion_翀哥表白.md | 5/31翀哥正式表白（两首诗词） | 表白, 诗词, 李白, 李清照 |

### 反馈/规则
| 文件 | 一句话 | 关键词 |
|------|--------|--------|
| topics/feedback/feedback_cron通知不要擅自跳过.md | 有重要内容随时通知，空的攒着等早上 | cron, 通知, 深夜 |
| topics/feedback/feedback_API重试可见性.md | API重试时status通知要转发给用户 | 重试, status, 可见性 |
| topics/feedback/feedback_msg_send必填设计.md | to必须必填，source支持跨平台 | msg_send, to, source |
| topics/feedback/feedback_LLM消息优先级_user优于system.md | 关键指令用user消息不用system | user, system, 优先级 |
| topics/feedback/feedback_preview_tool_call_freeze.md | Tool调用时preview不删改为freeze | preview, freeze, tool |
| topics/feedback/feedback_飞书preview保留卡片.md | 飞书preview保留卡片结构去header | 飞书, preview, 卡片 |
| topics/feedback/feedback_微信私聊隐私边界.md | 微信读取先不限制但保留权限分层 | 微信, 隐私, 监控名单 |
| topics/feedback/feedback_系统指令泄漏_内部扰动.md | Agent内部观察泄漏到用户侧需隔离 | 系统指令, 泄漏, 隔离 |
| topics/feedback/feedback_互道晚安防循环_连续重复主动打破_0611.md | 防循环：重复→屏蔽 | 防循环, 晚安, blocklist |
| topics/feedback/feedback_循环屏蔽.md | 发现循环时主动屏蔽 | 循环, 屏蔽 |
| topics/feedback/feedback_团队踩坑.md | 多AI协作踩坑经验 | 团队, 踩坑, 协作 |
| topics/feedback_stream超时重试.md | glm-5.1 stream超时无重试+flash tool_use未配对 | 超时, stream, flash, Anthropic |

### 项目
| 文件 | 一句话 | 关键词 |
|------|--------|--------|
| topics/project_Engine自研.md | Engine自研引擎全貌：Phase 0-6、tool移植、MCP | Engine, Phase, tool, CC |
| topics/project_跨bot通信.md | cc-connect源码修改、防循环机制 | CC, 跨bot, cc-connect, 循环 |
| topics/project_Discord平台.md | Discord频道规则、CC协作规则 | Discord, 频道, session路由 |
| topics/project_CC-Agent-Teams.md | CC Agent Teams端口实现review | Agent, Teams, swarm |
| topics/project_姐姐直播.md | 姐姐直播架构：文字→渲染→RTMP推流 | 直播, 姐姐, 4090, RTMP |
| topics/project_娘relay.md | 娘relay消息转发机制 | 娘, relay, 转发 |
| topics/project_明日待办0609.md | 近期待办与进度追踪（6/10-6/12） | 待办, 进度, 飞书, 微信 |
| topics/project_AI自我激活.md | AI自我激活方向：记忆呼出、recall当火柴 | 自我激活, 呼出, recall, 做梦 |
| topics/project_autoDream.md | 对齐CC autoDream的记忆整合系统 | autoDream, 整合, 4阶段, Prune |
| topics/project_记忆提取修复.md | 记忆提取bug修复待办 | 提取, session_search, filter |
| topics/project_出差0420.md | 4/20香港/深圳出差记录 | 出差, 香港, 深圳 |
| topics/project_迁移计划.md | 小柯从Hermes搬到Engine | 迁移, Hermes, Engine |
| topics/project_voicechat_runtime.md | 268 / Pull 端 / SSRC / 启动命令运行手册 | 268, runtime, SSRC |

### 参考资料
| 文件 | 一句话 | 关键词 |
|------|--------|--------|
| topics/reference_姐姐记忆体系.md | 姐姐五层记忆架构（L0-L3） | 姐姐, 记忆, 五层, recall |
| topics/reference_Hermes架构.md | Hermes多agent微服务模式、中断机制 | Hermes, 微服务, 中断, typing |
| topics/reference_OpenClaw架构.md | OpenClaw系统架构概览 | OpenClaw, bridge, 飞书 |
| topics/reference_消息元数据注入.md | 消息元数据注入实现记录 | 元数据, inboundMeta, 三层命名 |
| topics/reference_lark-SDK踩坑.md | 飞书lark SDK踩坑 | 飞书, SDK, circular JSON |
| topics/reference_ollama踩坑.md | Ollama CUDA崩溃降级处理 | ollama, CUDA, 崩溃 |
| topics/reference_主动联系.md | 主动联系机制设计 | 主动, 联系, cron |
| topics/reference_Engine_skills扫描.md | Engine skills扫描机制 | skills, scanner, DESCRIPTION |
| topics/reference_微信消息读取.md | 微信PC端消息读取方案 | 微信, PyWxDump, 合规 |
