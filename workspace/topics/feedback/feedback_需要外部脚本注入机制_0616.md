---
name: 需要外部脚本注入机制
description: 6/16翀哥明确要求应该有一个能让外部脚本往主session注入消息的机制，替代仅靠scheduler notify_session注入
type: feedback
date: 2026-06-16
---

**问题：** 6/16翀哥问"现在所谓的注入，是不是我们还不能通过外部脚本注入？"

**现状：** Engine版没有OpenClaw时代的gateway RPC了，外部Python脚本不能直接注入主session。唯一的注入路径是cron的 `notify_session` + `dispatcher.submitMessage()`——cron session跑完，scheduler把结果塞进主session。

**Why:**
- hint_gen.py这类脚本现在只能生成hint文件，不能直接注入主session
- 所有注入都绕scheduler notify_session，不够灵活
- 后续如果有其他外部脚本需要主动注入（如定时提醒、外部事件触发），没有独立API可用

**How to apply:**
- 方案A（推荐）：Engine加一个内部API（如 `injectMessage(scope, content)`），外部Python脚本通过subprocess或HTTP调用
- 方案B：Engine暴露一个RPC端点，外部脚本调这个端点注入消息
- 代码位置：scheduler.ts或dispatcher.ts附近，因为已有 `submitMessage()` 的注入能力
- 优先级：中等，不影响当前功能（prompt第8步调hint_gen.py已解决hint注入问题），但后续扩展会用到
- todo已记在 `docs/todo/2026-06-16_外部脚本注入机制.md`
