---
name: anthropic-provider toolUseBlocks重复yield bug
description: 6/16发现content_block_stop yield tool_call后没delete，finally兜底会重复yield同一个tool call → 已修复（commit 7970be8）
type: feedback
date: 2026-06-16
---

**问题：** anthropic-provider.ts第314-330行，`content_block_stop` yield tool_call后没有 `toolUseBlocks.delete(data.index)`。正常情况下`message_delta`来后`doneYielded=true`，finally跳过不触发。但API中途断连（1305等）时，finally兜底遍历剩余的toolUseBlocks再次yield——同一个tool call被yield两次。

**根因：** 用Map存tool call block（key=index），正常流程是：
1. `content_block_start` → 创建block → `toolUseBlocks.set(index, block)`
2. `content_block_delta` → 累积 `input_json_delta`
3. `content_block_stop` → yield tool_call（`toolUseBlocks.get(index)`）
4. `message_delta` → `doneYielded=true`

但第3步yield后没删map条目，如果API在第4步之前断连，finally遍历所有block再次yield。

**已修复（6/16 14:35，commit 7970be8）：** content_block_stop yield完后加 `toolUseBlocks.delete(data.index)`。今天去掉了`clone()`改用Map直接操作，删前先读store再删，删后取block用。翀哥看完确认是bug并让提交。

**How to apply:**
- 流式解析中，yield完整结果后立即从中间map删除条目
- 用"yield完就删"模式防止兜底逻辑重复产出
- 任何`finally`兜底遍历Map的场景，先确认Map里存的都是"还没处理过的"
