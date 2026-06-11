---
name: LLM消息优先级 — user消息优于system
description: 需要LLM重视并执行的关键指令（HEARTBEAT心跳、Pre-compaction flush等）必须用user消息而非system消息注入上下文，因为LLM（尤其小模型）容易忽略system消息
type: feedback
keywords: [user消息, system消息, LLM, 优先级, HEARTBEAT, PreCompact, flush, 注入]
created: 2026-06-11
---

## 规则

对LLM的关键操作指令，用`msg.user()`注入上下文，不要用`msg.system()`。跟HEARTBEAT一样的处理方式。

**Why:** 翀哥指出system消息容易被LLM（尤其小模型）忽略，user消息更受重视、更可能被执行。HEARTBEAT心跳已经用user消息了，Pre-compaction flush也应该一样。

**How to apply:** 任何需要LLM**主动执行**的指令（存档、flush、检查待办、写文件等），都用user消息注入。system消息只放静态规范/角色设定（AGENTS.md规则、MEMORY.md知识等），不做动态指令载体。

**已应用场景：**
- HEARTBEAT心跳 → `msg.user()`（之前的约定）
- Pre-compaction flush → `msg.user()`（6/11白天从system改为user）
