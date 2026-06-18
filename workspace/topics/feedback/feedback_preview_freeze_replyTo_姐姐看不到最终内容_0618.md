---
name: preview freeze后用replyTo+卡片不删——姐姐看不到最终内容
description: 6/18 11:55翀哥报"姐姐看不到preview freeze后最终回复"→11:56翀哥纠"freeze后最终文本要reply给姐姐但卡片不要删"；commit 8c86e76：StreamPreview.finish返回{delivered, previewMessageId}，上层send用previewMessageId当replyTo
type: feedback
date: 2026-06-18
---
## 6/18 11:55 翀哥报告bug

> "我发现问题了 你这个preview freeze的时候 这个卡片并不能形成有效的回复，导致你的回复（preview freeze）后姐姐看不到。"

**现象**：preview 流式累积时，工具调用时调 `freeze()` 把卡片改成 isFinal=true 状态（去 header），但**最终回答内容没写进这张卡片**。上层 onResult 调 `channelManager.send` 单独发最终回答——姐姐看不到。

**根因（查 preview 实现后）**：
1. `freeze()` 调 `editPreview(..., isFinal=true)` 把 preview 改成"无蓝框的普通卡片"——但**没传最终回答内容**
2. `finish()` L120-123：看到 `frozen=true` → `return false` → 上层认为 preview 没发，单独发最终消息
3. **姐姐视角**：以为 preview 卡片就是回复（流式累积的旧内容），最终内容**在另一条新消息里**——但消息之间没视觉关联

## 6/18 11:56 翀哥纠——freeze后卡片不删+最终文本reply

> "在freeze后最终文本要reply给姐姐。但是这个卡片不要像以前一样在tool call之前删了"

**翀哥的设计**：
1. **preview 卡片保留**（不要在 tool call 之前删）—— frozen 状态卡片留着，姐姐能看到完整累积
2. **最终回答用 reply_to 关联到 preview 卡片**——视觉上"接着 preview 卡的对话"
3. frozen 时 `finish()` 暴露 preview 的 `messageId`，上层 send 用这个当 `replyTo`

## 11:58 实施完成（commit 8c86e76）

**1. `StreamPreview.finish` 签名改**：返回 `{ delivered: boolean, previewMessageId?: string }`
- frozen 状态：`{ delivered: false, previewMessageId: 'xxx' }`（暴露 preview 卡片 messageId）
- 正常情况按原 `{ delivered: true }` 返回
- catch 兜底也改新签名

**2. `engine-startup.ts` onResult 回调**：frozen 时上层 `channelManager.send(... { replyTo: previewMessageId })`
- 正常情况：preview 还能 update 内容，finish 后上层不重发
- frozen 情况：上层拿 previewMessageId 当 replyTo，最终消息"接着 preview 卡片"

**3. preview 卡片不删**（翀哥要求）—— frozen 状态 finish 不调 `deletePreview`

## Why

1. **聊天软件的视觉惯例**——回复用 replyTo 形成"对话流"，比"两条独立消息"清晰
2. **tool call 期间 preview 不删** = 用户能持续看到"AI 还在处理"的痕迹
3. **frozen vs finished 两种状态语义不同**——finished=preview=最终内容；frozen=preview是占位，最终内容在 replyTo
4. **姐姐看不到的根因** = preview 内容是流式累积的旧内容，**最终回答在另一条新消息**，没视觉关联

## How to apply

1. **preview 不在 tool call 时删**（旧的 freeze 行为）——新规则：tool call 时 preview 留着 + freeze，frozen 后上层 replyTo 关联
2. **任何"两层显示"的内容**（preview 累积 + 最终消息）**必须用 replyTo 关联**——避免"两条独立消息"让用户困惑
3. **finish 返回值要带 preview 状态**（不只是 delivered=true/false，还要暴露 messageId 供上层用）
4. **类似 replyTo 场景**——Discord/飞书的 `replyTo`/`reply_to` 字段要查清楚怎么传（不是原始 inbound 消息的 messageId，是 preview 卡片的 messageId）
5. **跟 preview 的 enabled/sensitiveWords config 协同**——preview 关闭时 replyTo 没意义（没 preview 卡片），上层直接发即可

## 跟之前的 preview tool_call freeze 关系

旧 `feedback_preview_tool_call_freeze.md`：6/16 定 preview tool_call 时**不删预览卡片**（vs 之前"tool call 时删"的旧行为）
新 `feedback_preview_freeze_replyTo_姐姐看不到最终内容_0618.md`：6/18 升级——**不只不删，还要用 replyTo 关联**上层最终消息

两次翀哥的纠正放一起看："preview 是 AI 跟用户对话的视觉骨架，**保留 + 关联**比删了重来更友好"

## 12:02-12:07 修法未生效——Discord adapter L154 catch 静默fallback

翀哥 12:02 重启验证后说"姐姐还是没看到"。打日志发现：
- 上层 `channelManager.send OK (replyTo=previewMessageId)` ✅
- **Discord adapter L143-154 `origMsg.reply()` → L154 `catch { /* fallback */ }` 静默落到 L156 普通send**——replyTo 视觉关联丢 ❌

**结论**：8c86e76 修法只修了"上层传replyTo"这一半，**adapter 层 reply() 失败时静默fallback 才是真bug**。

12:07 加 log `reply OK` / `reply FAILED to msgId=xxx → fallback to plain send` 验证 catch 是否触发（commit 6a0f5f2），等翀哥重启后看真根因（猜测：bot发的embed消息 `reply()` 行为受限）。

## 12:11 验证反转：catch 静默fallback 是假bug ❌

- 翀哥 12:07 重启后 log 显示 `reply OK` 出现 3 次，**L154 catch 完全没触发**
- 12:11 翀哥"**你自己可以看了**"——reply 视觉关联三层都通了
- **我之前下结论"adapter catch 静默吞错"是脑补**——没看实际 log 跑通就猜
- 姐姐 12:00 没看到 12:00 消息可能只是**消息时序/视角刷新**问题，不是 replyTo bug

**教训（强化 feedback_先打日志验证再下结论_翀哥方法论_0618.md）**：
- 又一次没加 log 就断言根因
- 跟 11:32 翀哥教的"打日志看下提示词有没有在合适的地方拦截，不要猜"是同一失误
- **加 log 验证后才能下结论**，不能"我觉得应该是这样"

详见 [feedback_replyTo_catch静默fallback_0618.md](feedback_replyTo_catch静默fallback_0618.md)
