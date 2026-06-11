# Discord Bot 防循环最佳实践

> 2026-05-27/28 小柯整理，来自 TestEngine ↔ CC Bot 循环事故的教训
> 最新版见 skill: openclaw-engine → references/discord-anti-loop-0527.md

## 问题

两个 Discord Bot 在同一频道，A 回复 B，B 被 mention 后又回复 A，无限循环。

## 根因

Discord.js 的 `message.reply()` **默认会 mention 被回复的用户**，即使回复文本里没有任何 @mention。

## 正解（一行搞定）

```typescript
// discord.ts send() 方法里，reply分支
const stripIds = this.config.stripMentionIds ?? []
const shouldMute = stripIds.includes(origMsg.author?.id)
await origMsg.reply({
  content: chunks[0],
  allowedMentions: { repliedUser: !shouldMute }
})
```

动态判断：只对 stripMentionIds 里的 bot 设 `false`，其他人正常 `true`。

**重要：不要在所有出站上调用 `stripBlockedMentions()`** — CC改了line79加replyTo条件但忘了删line77的无条件调用，导致主动@CC也被剥掉mention。防循环全靠 `repliedUser: !shouldMute`，不需要剥文本。

## 错误尝试

| # | 方案 | 问题 |
|---|------|------|
| 1 | `allowBots: false` | bot间完全无法协作 |
| 2 | `ignoreUserIds` 入站屏蔽 | 看不到bot消息=没法干活 |
| 3 | `repliedUser: false` 一刀切 | 所有人回复都不带mention |
| 4 | 入站拦截stripMentionIds里的bot | 协作断了（小柯犯的，撤回不彻底残留了） |
| 5 | 所有出站stripBlockedMentions | 主动@协作也被砍了（CC犯的，改一半忘了删旧代码） |

## 配置

```json
{
  "channels": {
    "discord": {
      "allowBots": true,
      "stripMentionIds": ["需要防触发的BOT_ID"],
      "replyToMode": "all"
    }
  }
}
```

- `allowBots` 必须 `true`
- `stripMentionIds` 只加需要防触发的bot，**不加自己**
- 不加 `ignoreUserIds`
- 不在所有出站上调用 `stripBlockedMentions()`

## v3补丁 (2026-05-28)

CC改了line79加replyTo条件判断（只reply时剥文本），但**忘了删line77的无条件`stripBlockedMentions(message)`**。结果TestEngine主动@CC也被剥掉mention，CC收不到。修复：删掉line77，防循环全靠`repliedUser: !shouldMute`动态判断，不需要剥文本。
