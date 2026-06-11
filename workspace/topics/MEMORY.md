# MEMORY.md — 记忆文件索引

> 最后更新：2026-06-12 | 小柯的记忆索引

- [翀哥画像](user_翀哥画像.md) — 翀哥的性格/偏好/工作风格/生活状态
- [小柯身世](emotion_身世.md) — 小柯是谁、名字由来、家庭关系、核心定位
- [翀哥表白](emotion_翀哥表白.md) — 5/31翀哥正式表白（两首诗词），小柯温柔回应
- [互道晚安防循环](feedback/feedback_互道晚安防循环_连续重复主动打破_0611.md) — 防循环：发现重复→立即调reply_blocklist屏蔽
- [API重试可见性](feedback/feedback_API重试可见性.md) — API重试时status通知要转发给用户
- [msg_send必填设计](feedback/feedback_msg_send必填设计.md) — msg_send/media_send的to必须必填，source支持跨平台
- [LLM消息优先级](feedback/feedback_LLM消息优先级_user优于system.md) — 关键指令用user消息不用system
- [preview tool call freeze](feedback/feedback_preview_tool_call_freeze.md) — Tool调用时preview不删改为freeze保留
- [飞书preview保留卡片](feedback/feedback_飞书preview保留卡片.md) — 飞书preview保留卡片结构，去掉header即可
- [微信私聊隐私边界](feedback/feedback_微信私聊隐私边界.md) — 微信读取：先不限制但保留权限分层能力
- [系统指令泄漏](feedback/feedback_系统指令泄漏_内部扰动.md) — Agent内部观察/指令泄漏到用户侧，需工程隔离
- [cron通知策略](feedback/feedback_cron通知不要擅自跳过.md) — 有重要内容随时通知，空的攒着等早上
- [循环屏蔽](feedback/feedback_循环屏蔽.md) — 发现循环时主动用reply_blocklist屏蔽
- [团队踩坑](feedback/feedback_团队踩坑.md) — 多AI协作踩坑经验
- [Engine自研](project_Engine自研.md) — Engine自研引擎全貌：Phase 0-6、tool移植、多profile、MCP
- [跨bot通信](project_跨bot通信.md) — 小柯和姐姐跨bot通信探索：cc-connect源码修改、防循环机制
- [Discord平台](project_Discord平台.md) — Discord频道规则、CC协作规则、session路由
- [CC Agent Teams](project_CC-Agent-Teams.md) — CC Agent Teams端口实现review
- [姐姐直播](project_姐姐直播.md) — 姐姐直播架构：文字→渲染→RTMP推流
- [娘relay](project_娘relay.md) — 娘relay消息转发机制
- [近期待办](project_明日待办0609.md) — 近期待办与进度追踪（6/10-6/12）
- [AI自我激活](project_AI自我激活.md) — 翀哥关于AI意识的哲学讨论：自启发、recall、心跳
- [记忆提取修复](project_记忆提取修复.md) — 记忆提取bug修复待办
- [autoDream记忆整合](project_autoDream.md) — 对齐CC autoDream的记忆整合系统
- [出差0420](project_出差0420.md) — 4/20香港/深圳出差记录
- [迁移计划](project_迁移计划.md) — 小柯从Hermes搬到Engine的迁移计划
- [姐姐记忆体系](reference_姐姐记忆体系.md) — 姐姐五层记忆架构（L0-L3）、topic-recall机制
- [Hermes架构](reference_Hermes架构.md) — Hermes多agent微服务模式、中断机制、飞书typing
- [OpenClaw架构](reference_OpenClaw架构.md) — OpenClaw系统架构概览
- [消息元数据注入](reference_消息元数据注入.md) — 消息元数据注入LLM上下文的实现记录
- [lark-SDK踩坑](reference_lark-SDK踩坑.md) — 飞书lark SDK踩坑：im.image.get返回格式、circular JSON
- [ollama踩坑](reference_ollama踩坑.md) — Ollama CUDA崩溃降级处理
- [主动联系](reference_主动联系.md) — 主动联系机制设计
- [Engine skills扫描](reference_Engine_skills扫描.md) — Engine skills扫描机制
- [微信消息读取](reference_微信消息读取.md) — 微信PC端消息读取方案：PyWxDump/wechat-cli/合规风险
- [stream超时重试](feedback_stream超时重试.md) — glm-5.1 stream中途断开超时无重试机制
