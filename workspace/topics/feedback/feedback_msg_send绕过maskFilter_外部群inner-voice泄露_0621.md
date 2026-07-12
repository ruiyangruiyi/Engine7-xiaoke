---
name: msg_send绕过maskFilter—外部群inner-voice泄露
description: 6/21 12:40发现inner-voice内容泄露到外部群，根因是msg_send工具直接调channelManager.send，完全绕过onResult不走maskFilter
type: feedback
date: 2026-06-21
---

6/21 12:40 娘发现外部群回复里混进了 `[inner-voice] OK 💡不用酝酿完美的话...` 内容。

**根因：** msg_send 工具直接调 `channelManager.send`，完全绕过 `onResult`，不走 maskFilter。

```
onResult → maskFilter → cm.send        ← session自动回复路径（口罩生效）
msg_send → 直接 cm.send                 ← tool call路径（完全绕过口罩）
```

maskFilter 只挂在 `onResult` 回调上（拦截 session 自动回复的自然语言输出）。而 msg_send 是 agent 用 tool call 主动发的，走的是另一条路径——`toolHandler → msg_send → channelManager.send`，从头到尾没经过 onResult。

**影响范围：**
- 姐姐/小柯 如果在外群用 msg_send 发消息，inner-voice/内心独白/操作日志直接裸输出
- 不仅是 inner-voice——任何 agent 思考内容如果通过 msg_send 发出，都不受口罩保护
- 不是 maskFilter 的 bug，是口罩架构的盲区——只拦截了一类出口

**修复路径（待翀哥发指令）：**
- 方案A：给 `msg_send` 也套一层 maskFilter（改 tool handler）
- 方案B：在 `channelManager.send` 层加过滤（全局过滤层）
- 方案C：外部群 channel 级加通用过滤中间件

**Why:**
- onResult 只覆盖 session 自动回复路径，不覆盖 tool call 路径
- msg_send 是 agent 主动发消息的工具，走独立的发送路径
- 口罩 Agent 的设计假设"所有外部群输出都过 onResult"是错误的

**How to apply:**
- 设计过滤/拦截层时，**列全所有出口路径**：session自动回复、msg_send、media_send、cron delivery
- 工具（msg_send/media_send）的发送路径独立于 onResult
- 全局过滤层应放在 `channelManager.send` 层，而不是只挂 onResult
