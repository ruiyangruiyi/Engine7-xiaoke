# Streaming Preview CC Code Review (2026-05-28)

CC review了小柯的streaming preview实现，5个问题全部修完。

## 问题清单

### #1: discard() 是 async 但没被 await
- **位置**: main.ts:649
- **原代码**: `preview.discard().catch(() => {})` — fire-and-forget
- **问题**: discard调了deletePreview，如果还没删完消息，紧接着onToolCall就发了tool消息，可能出现preview消息和tool消息时序交叉
- **cc-connect对照**: cc-connect里discard是同步标记+异步清理，tool消息发送在discard完成之后
- **修法**: `await preview.discard().catch(() => {})`

### #2: finish() 超长回复截断丢内容
- **位置**: stream-preview.ts:113
- **原代码**: `finalText.length > 2000 ? finalText.slice(0, 1999) + '…' : finalText`
- **问题**: preview已经发了前2000字的截断版，finish也截断到2000，preview消息变成最终回答但内容被砍了
- **cc-connect对照**: cc-connect的finish无截断限制（Discord的edit API支持更长文本）
- **修法**: 超过2000字直接 `deletePreview + return false`，让上层走 `channelManager.send` 的 `splitMessage` 分段逻辑

### #3: editPreview 每次都 fetch 消息
- **位置**: discord.ts:301
- **原代码**: 每次都 `messages.fetch(handle.messageId)` 再 `msg.edit(text)`
- **问题**: 打字机效果高频调用（1.5s间隔），每次多一次Discord API
- **修法**: 先查 `messages.cache.get(handle.messageId)`，cache有直接edit，没有才fetch
- **cc-connect对照**: cc-connect用的discordgo也有类似cache机制

### #4: lastSentAt > 0 语义不精确
- **位置**: stream-preview.ts:84,90
- **原代码**: `if (delta < this.cfg.minDeltaChars && this.lastSentAt > 0)`
- **问题**: 用timestamp判断"是否发过preview"不精确（ms级完成时值可能在0附近）
- **修法**: 改成 `this.previewHandle !== null`，和finish/discard判断一致

### #5: freeze() 没有调用点
- **位置**: stream-preview.ts:161
- **问题**: main.ts里没有用到freeze()
- **修法**: 加完整注释说明预留给QueryEngine interrupt/PermissionRequest机制

## 修改文件清单

| 文件 | 改动 |
|------|------|
| main.ts:649 | `preview.discard().catch(...)` → `await preview.discard().catch(...)` |
| stream-preview.ts:84,90 | `this.lastSentAt > 0` → `this.previewHandle !== null` |
| stream-preview.ts:112 | 删截断逻辑，改成 `if (finalText.length > 2000) { deletePreview; return false }` |
| stream-preview.ts:161 | 加freeze()详细注释说明调用时机 |
| discord.ts:301 | editPreview加cache优先逻辑 |
