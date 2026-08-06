---
name: 外部脚本注入机制
description: 6/16翀哥提出Engine需要外部脚本往主session注入消息的机制，替代仅靠scheduler notify_session
type: project
---

**背景：** 6/16翀哥发现"所谓的注入"在两版引擎中不同，指出需要有外部脚本注入机制。

**现状（Engine版）：**
- OpenClaw版通过gateway RPC让外部脚本直接注入主session
- Engine版砍了gateway，外部脚本不能直接注入
- 唯一注入路径是cron的 `notify_session` + `session_message` — cron session跑完，scheduler把结果塞进主session

**待实现方案（两种）：**
1. **轻量版：** Engine开一个local HTTP endpoint，外部Python脚本可以POST消息进来，Engine通过 `dispatcher.submitMessage()` 注入
2. **完整版：** 类似OpenClaw的gateway RPC，支持认证和路由

**Why:** 姐姐的inner-voice内心独白功能依赖外部脚本注入——hint_gen.py生成念头+💡hint后需要放进主session。没有外部注入机制，hint只能靠cron notify_session带进去，灵活性受限。

**How to apply:**
- 见 `docs/todo/2026-06-16_外部脚本注入机制.md` 详细文档
- 实现前先读 `docs/research/` 下相关调研
