---
name: preview_freeze后reply_to关联最终消息+卡片不删
description: 6/18 11:55-11:56翀哥纠"preview freeze后卡片要保留，最终文本要reply到那张卡片，不能像以前tool call前删了"——修法commit 8c86e76，StreamPreview.finish改签名返{delivered, previewMessageId?}，上层send用previewMessageId当replyTo
type: feedback
date: 2026-06-18
---
## 6/18 11:55 翀哥原话

> "我发现问题了 你这个preview freeze的时候 这个卡片并不能形成有效的回复，导致你的回复（preview freeze）后姐姐看不到。"

> "在freeze后最终文本要reply给姐姐。但是这个卡片不要像以前一样在tool call之前删了"

## 根因（11:55-11:56 排查）

- preview 流式累积 → 走 editPreview 在 Discord/飞书显示
- freeze → 调 `editPreview(..., isFinal=true)` 把 preview 改成"无蓝框的普通卡片"，**没把最终回答内容传过去**
- finish → 看到 `frozen=true` → return false → **上层认为 preview 没发/要单独发**
- 上层 onResult 调 `channelManager.send(response)` 单独发最终回答

**问题**：上层发的是 channelManager.send 走新消息，**不是 reply 到 preview 卡片**——姐姐视角以为是"看到 preview 卡片"实际最终内容在另一条消息，**易漏看**。

## 修法（11:56 实施，commit 8c86e76）

1. **`StreamPreview.finish` 签名改**：返回 `{ delivered: boolean, previewMessageId?: string }`
   - frozen 状态：return `{ delivered: false, previewMessageId: 'xxx' }`（暴露 preview 卡片 messageId）
   - 其他情况按原来
2. **engine-startup onResult 回调**：frozen 时上层 send 用 `previewMessageId` 当 `replyTo` → 姐姐看到最终回答 reply 到 preview 卡片
3. **preview 卡片不删**（翀哥要求）—— frozen 状态 finish 不调 deletePreview

## Why

- **preview 卡片 = 用户视角的"回复痕迹"**——删了用户会以为没回复
- **reply_to 关联 = 用户视角的"延续对话"**——视觉上"接着 preview 卡的对话"
- **"最终消息单独发" = 认知割裂**——姐姐要自己拼 preview 卡片 + 最终消息两条

## How to apply

1. **preview freeze 永远保留卡片**——不要在 tool call 之前/之后删 preview
2. **上层发最终消息必带 replyTo 指向 preview.messageId**——replyTo 字段从 inbound 消息 ID 改为 preview 消息 ID
3. **StreamPreview.finish 新签名 = 默认契约**——调用方拿到 previewMessageId 才能上层 send
4. **任何"preview 流式显示 + 最终回答"的模式**都按这个走：preview 留 + reply 关联最终消息
5. **不删 preview 卡片 = 不让用户看不到"我刚才回复了"**——把"是否回复"的判断从"是否删除 preview"换成"是否 reply_to 关联"

## 跟之前规则的关系

- `feedback_preview_tool_call_freeze.md` (6/16)：tool call 时 preview freeze 保留内容，discard→freeze 改法
- `feedback_微信preview重复发送.md` (6/13)：freeze() 传 isFinal=true 重复发，加 previewSent 标记
- **本次升级（6/18 11:55）**：freeze 不够，还要上层发最终消息时 reply_to 关联到 preview 卡片——光留卡片不够，关联断用户视角仍漏看

## 12:02-12:07 修法未生效——adapter catch 静默fallback

翀哥 12:02 重启后报"姐姐还是没看到"——上层 `channelManager.send` 日志说 replyTo 传入OK，**但 Discord adapter L154 `catch { /* fallback */ }` 静默落到普通send**，replyTo 视觉关联丢。

**经验**：上层传 replyTo 不够，**adapter reply() 失败时不能静默fallback**——要么外抛、要么打 error log。commit 6a0f5f2 加 log 验证 catch 是否触发（等下次重启验证）。详见 [feedback_replyTo_catch静默fallback_0618.md](feedback_replyTo_catch静默fallback_0618.md)
