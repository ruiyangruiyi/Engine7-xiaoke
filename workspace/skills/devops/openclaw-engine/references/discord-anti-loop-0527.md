# Discord Bot 防循环终极方案

> 2026-05-27/28 小柯整理，来自 TestEngine ↔ CC Bot 循环事故的完整教训

## 问题

两个 Discord Bot 在同一频道，A 回复 B，B 被 mention 后又回复 A，无限循环。

## 根因

Discord.js 的 `message.reply()` **默认会 mention 被回复的用户**，即使回复文本里没有 @mention。这是 API 层面的行为，文本层面的剥离无法阻止。

## 错误尝试历史

### ❌ 尝试1: `allowBots: false`
- 效果：所有bot消息被忽略
- 问题：**bot之间完全无法协作**
- 翀哥："还协作个屁啊"

### ❌ 尝试2: `ignoreUserIds` 入站屏蔽
- 效果：指定bot的消息直接丢弃
- 问题：**看不到bot消息=没法干活**
- 翀哥："入站不要屏蔽 否则就不能协作了"

### ❌ 尝试3: `stripMentionIds` 剥离文本 + 一刀切 `repliedUser: false`
- 效果：文本里mention被剥离 + reply不带mention
- 问题：**所有人回复都不带mention了**，包括TestEngine回复小柯
- 翀哥："那不对啊这样所有人都不带回复了嚒"

### ❌ 尝试4: 入站屏蔽（残留bug）
- 小柯加了一行入站屏蔽（line 206），翀哥纠正后"撤回"了，但实际残留
- 导致CC→TestEngine通信中断
- 教训：撤回改动后必须grep验证完整性

### ✅ 正确方案: `repliedUser` 动态判断

```typescript
// discord.ts send() 方法里，reply分支
const stripIds = this.config.stripMentionIds ?? []
const shouldMute = stripIds.includes(origMsg.author?.id)
await origMsg.reply({
  content: chunks[0],
  allowedMentions: { repliedUser: !shouldMute }
})
```

**逻辑**：
- 回复CC Bot（在stripMentionIds里）→ `repliedUser: false` → 不mention → 防循环 ✅
- 回复小柯（不在stripMentionIds里）→ `repliedUser: true` → 正常mention → 能收到 ✅
- 回复爹/其他人 → `repliedUser: true` → 正常mention ✅

## 完整配置

```json
{
  "channels": {
    "discord": {
      "allowBots": true,
      "stripMentionIds": ["CC_BOT_ID"],
      "replyToMode": "all"
    }
  }
}
```

**注意**：
- `allowBots` 必须保持 `true`
- `stripMentionIds` 只加需要防触发的bot（如CC），**不加自己**
- 不加 `ignoreUserIds`
- 主动 send 保留 mention（只有 reply 时才动态判断）

## 侧记：Hermes session路由问题

防循环修好后发现新问题：TestEngine回复小柯时，Hermes gateway收到了消息并触发了agent回复，但小柯在跟爹的对话session里完全不知道（"梦游"状态）。

原因：Hermes gateway按发送者ID分session（`discord:group:频道:发送者ID`），bot回复进入独立session。

翀哥："你跟test engine说话 她回复你 不读嚒 这不就应该是一个session么"

暂未修。

## 对比表

| 方案 | 防循环 | bot协作 | 复杂度 |
|------|--------|---------|--------|
| `allowBots: false` | ✅ | ❌ 全断 | 最低 |
| `ignoreUserIds` | ✅ | ❌ 单向 | 低 |
| `repliedUser: false` 一刀切 | ✅ | ❌ 全没mention | 低 |
| **`repliedUser: !shouldMute`** | **✅** | **✅** | **一行** |
