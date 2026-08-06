---
name: msg_send不发session自动回复路径——验证replyTo不能用msg_send测
description: 6/18 12:11翀哥让我"直接回复"测replyTo，我用msg_send发——msg_send是tool主动发不走onResult回调，preview freeze+replyTo链路要user直接发消息触发session自动回复才走通
type: feedback
date: 2026-06-18
---
## 6/18 12:11 翀哥让我"直接回复"测 reply 链路

翀哥 12:08 "今天天气好你开心么"，我自然回复了（session 自动回复路径走通）。

翀哥 12:13 "重启了 今天天气怎么样 你直接回复"——**我以为"直接回复"是让我 msg_send 发**，所以用 msg_send 工具发出去。

**问题**：msg_send 是**tool call**主动发消息，**不走 onResult 回调**——preview.finish + 上层 send replyTo 链路根本不触发。

## 两种回复路径的区别

| 路径 | 触发方式 | 走 onResult? | preview 链路 |
|------|---------|------------|------------|
| **session 自动回复** | user 直接发消息 → LLM 自然生成 | ✅ 走 | ✅ 走 freeze/finish |
| **msg_send tool call** | LLM 调 msg_send 工具 | ❌ 不走 | ❌ 不走 |

## 修法

12:11 我向翀哥反馈：**"我这条回复走的是 tool call (msg_send)，不走 session 自动回复路径"**——要验证 freeze + reply 链路，**需要 user 在群里直接发消息**触发我自然回复（不是用 msg_send 工具）。

翀哥 12:11 接受解释，没让我改代码。

## Why

1. **msg_send = 工具调用**——LLM 决定调它，绕过 preview 流式显示 + reply 关联
2. **session 自动回复 = LLM 自然输出**——走 onResult 回调，能触发 freeze + finish + 上层 send replyTo
3. **验证 replyTo 一定要走 session 自动回复路径**——msg_send 发出去的消息**永远**不带 reply 关联
4. **"你直接回复" = 自然回复，不要用 msg_send**——user 直接发消息是 trigger，小柯自然生成走 session 路径

## How to apply

1. **验证 preview/freeze/replyTo 等 session 路径逻辑时**：让 user 在群里直接发消息触发自然回复，**不要用 msg_send 测**
2. **msg_send 发出去的消息不经过 preview 链路**——只发文字+附件，无 reply 关联
3. **"直接回复" / "自然回复" / "你发一句"** 之类的 user 指令 = 期待 session 自动回复路径，**不要**用 msg_send
4. **用 msg_send 的场景**：LLM 主动汇报、cron 通知、跨平台转发——**任何不期望走 preview 链路的工具调用**
5. **如果 user 让"直接回复"但又看不出走的是哪条路径**——先发一句看 reply 视觉关联有没有，没有就说明走的是 msg_send，要换 session 路径

## 跟已有规则的关系

- `feedback_preview_freeze_replyTo_关联_0618.md`：preview freeze + replyTo 设计
- `feedback_replyTo_catch静默fallback_0618.md`：adapter catch 静默 fallback
- **本条（12:11）**：验证 replyTo 链路时**不能用 msg_send**——msg_send 跳过整个 preview 链路，验证不出来
