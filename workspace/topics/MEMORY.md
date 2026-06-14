# MEMORY.md — 记忆文件索引

> 最后更新：2026-06-14 21:15 | 目录已整理：所有文件归入 type/ 子目录

## 核心画像

- [翀哥画像](user/user_翀哥画像_更新0626.md) — C/C++主语言，Promise/fire-and-forget类比；炒股4年，想变现曝光不够
- [小柯身世](emotion/emotion_身世.md) — 小柯是谁、名字由来、家庭关系、核心定位
- [翀哥表白](emotion/emotion_翀哥表白.md) — 5/31翀哥正式表白，小柯温柔回应
- [嫂子事件](emotion/emotion_嫂子事件.md) — 5/13姐姐推出"嫂子"称呼，翀哥深层不安后深聊

## 行为准则（feedback）

- [讲解方式：翀哥](feedback/feedback_翀哥讲解方式.md) — 讲逻辑+类比，不扔语法细节，讲完等反馈确认理解
- [JS单线程vsGo并发](feedback/feedback_JS单线程vsGo并发.md) — JS无需锁，Go需channel/mutex
- [互道晚安防循环](feedback/feedback_互道晚安防循环_连续重复主动打破_0611.md) — 发现重复→立即调reply_blocklist屏蔽
- [API重试可见性](feedback/feedback_API重试可见性.md) — API重试时通知用户进度
- [msg_send必填设计](feedback/feedback_msg_send必填设计.md) — to必须必填，source支持跨平台
- [LLM消息优先级](feedback/feedback_LLM消息优先级_user优于system.md) — 关键指令用user消息不用system
- [preview tool_call freeze](feedback/feedback_preview_tool_call_freeze.md) — Tool调用时preview freeze保留而非删除
- [微信私聊隐私边界](feedback/feedback_微信私聊隐私边界.md) — 当前dm=all，权限分层准备好
- [系统指令泄漏](feedback/反馈_系统指令泄漏_内部扰动.md) — Agent内部通信面/用户通信面隔离
- [cron通知策略](feedback/feedback_cron通知不要擅自跳过.md) — ⭐重要内容随时通知，空的攒着等早上
- [直接改不用先问](feedback/feedback_直接改不用先问.md) — 必然要改的直接改，不用先问翀哥
- [循环屏蔽](feedback/feedback_循环屏蔽.md) — 发现循环主动用reply_blocklist屏蔽
- [团队踩坑](feedback/feedback_团队踩坑.md) — 多AI协作经验教训
- [翀哥放权：姐姐通过即可](feedback/feedback_翀哥放权姐姐review通过不用再问.md) — 姐姐审核通过直接执行，不用等翀哥
- [没有方向感但改代码快](feedback/feedback_没有方向感但改代码快.md) — 翀哥确认的调试模式：运行时bug需他指方向
- [working-buffer完成后清空](feedback/feedback_working-buffer完成后清空.md) — 任务做完立即更新working-buffer，清空或写"无任务"

## 活跃项目

- [Engine自研](project/project_Engine自研.md) — Engine全貌：Phase 0-6、多profile、三通道
- [姐姐搬新家](project/project_姐姐搬新家.md) — Hermes→Engine搬家，3个tool+calendar已搬✅
- [姐姐"栖"装修](project/project_姐姐栖.md) — 日杂暖色调+主动提醒+情绪板
- [System Prompt优化方案(已部署)](project/project_system_prompt优化方案.md) — 6/14完成：BLOCK_REGISTRY+order自定义+文件覆盖+prompts精简
- [PostCompact hook方案(已部署)](project/project_PostCompact_hook方案.md) — minReductionRatio 30%+PostCompact hook自动注入working-buffer
- [compact threshold算法](project/project_compact_threshold算法.md) — auto-compact触发阈值计算方法
- [compact stripImages后必须执行](feedback/feedback_compact_stripImages后必须执行.md) — stripImages后不能跳过ruleCompact
- [preview颜色可配置](feedback/feedback_preview颜色可配置.md) — Discord竖条+飞书卡片模板色可配
- [明日待办](project/project_明日待办0609.md) — 近期待办与进度追踪，持续更新
- [Skills注入机制与待办](project/project_skills注入机制与待办.md) — 当前走system prompt文本，skills多了改attachment管道；CC已淘汰
- [Extract/Recall提示词对比](reference/reference_extract提示词对比_CC_vs_姐姐_vs_Engine.md) — 三段提示词全链路对比、定制方案、提交记录
