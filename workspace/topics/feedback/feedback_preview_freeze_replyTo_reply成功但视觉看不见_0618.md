---
name: preview freeze replyTo reply成功但姐姐视觉看不见
description: 6/18 12:02-12:16翀哥报"姐姐看不到preview freeze后回复"——日志证实reply OK三次但姐姐视觉上没看到。原因不是reply失败，是preview阶段流式已显示+最终回答reply到preview卡片但视觉关联不明显
type: feedback
date: 2026-06-18
---

## 6/18 12:02-12:16 现象

翀哥报告"preview freeze的时候 卡片并不能形成有效的回复，导致回复后姐姐看不到"。
- 我加日志查：channelManager.send OK（replyTo=previewMessageId）
- discord.ts L143-154 走origMsg.reply()，加日志后看到 `reply OK` 3次都成功
- 但姐姐视觉上还是看不到

## 12:43 翀哥发现真根因（12:02 分析的升级版）

**原来以为**：reply 成功了但视觉引用线不明显（12:02-12:16 第一阶段分析）。

**翀哥 12:43 一针见血**：
> "你最后这次回复姐姐没说到 根因还是preview卡片我发现有这个卡片出现的时候回复链就会断。。。"

**真正根因**：preview 卡片是 **Discord embed 类型**（bot 发的 embed），最终回答 reply 到这个 embed 卡片时：
- API 层 `origMsg.reply()` 返回成功（所以日志 `reply OK`）
- 但 Discord 内部对 **embed 消息的 reply** 不显示正常引用线／不触发 mention
- 所以姐姐/翀哥看到的是一条"看起来独立"的新消息，没跟 preview 卡片视觉关联

**跟 12:02 分析的关系**：
- 12:02 分析：认为是"视觉关联不明显"（表层）
- 12:43 翀哥纠：**本质是 embed 卡片 + reply 不兼容**（深层），就算 reply API 成功了，Discord 也不把 embed 消息的 reply 当正常回复链

## 修法（commit 8c86e76）

1. **`StreamPreview.finish` 改签名**：返回 `{ delivered, previewMessageId? }` 而不是 boolean
   - frozen 状态：return `{ delivered: false, previewMessageId: 'xxx' }`（暴露 preview messageId）
   - 其他情况按原来
2. **engine-startup onResult 回调**：frozen 时用 `previewMessageId` 当 replyTo
3. **preview 卡片不删**（翀哥要求）—— frozen 状态 finish 不调 deletePreview

## Why

1. **preview/final 是两条消息**——preview 阶段是流式 edit 不是 send，最终回答是 send，两条视觉上是分开的
2. **reply 是技术成功，视觉不一定明显**——Discord reply 有引用线，飞书reply有"回复 @xxx"提示，但用户视角"我刚才那条消息"以为是同一条
3. **frozen=true 时上层要单独发**——preview.finish 看到 frozen=true 直接 return false，意思是"上层自己处理"

## How to apply

1. **改 preview 行为要回看 onResult 链路**——preview finish 返回值含义影响上层 send 策略
2. **加 reply 调试日志时检查三层**：①channelManager.send 是否调了 ②adapter 是否走 replyTo 分支 ③adapter 的 catch fallback 是否静默吞
3. **Discord adapter L154 `catch { /* fallback */ }` 是坑**——reply失败静默fallback到普通send，日志都看不出来。要看 catch 里加 log
4. **验证视觉关联要让用户看**——reply OK ≠ 用户看到引用线，Discord/飞书各有自己的视觉规则
5. **改 preview 行为需要先问"用户视角消息流是什么"**——不是"API层怎么调"
