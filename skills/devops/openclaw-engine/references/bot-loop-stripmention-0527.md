# Bot互触循环 & stripMentionIds修复 (2026-05-27夜)

## 事件经过

1. **20:35** CC和TestEngine在CC频道互刷"在。"形成死循环
2. 原因：TestEngine `allowBots: true` + 没有任何消息过滤
3. 小柯改 `allowBots: false` → 被翀哥骂（断了所有bot协作）
4. 小柯把自己加到 `ignoreUserIds` → 又被翀哥骂（我自己被屏蔽了没法协作）
5. 正确方案：`allowBots: true` + `stripMentionIds: [CC_Bot]`

## 最终正确配置

```json
"channels": {
  "discord": {
    "allowBots": true,           // 必须true！断协作
    "stripMentionIds": ["1504373837880627280"],  // CC Bot — reply时剥离
    "ignoreUserIds": []          // ❌ 不要加！入站忽略会看不到消息
  }
}
```

## 教训

- `allowBots: false` = 所有bot消息都忽略，包括小柯at TestEngine，不可行
- `ignoreUserIds` = 自己也被屏蔽，不可行
- **正确：bot消息正常收正常处理，reply时用stripMentionIds把对方mention剥掉**

## 待修Bug：stripMentionIds无条件剥离

**位置**: `discord.ts:79`

**当前代码**:
```typescript
async send(target: string, message: string, options?: SendOptions): Promise<void> {
  let cleaned = this.stripBlockedMentions(message)  // ❌ 无条件剥离
  // ...
}
```

**问题**: 主动@某人也变成无mention了，无法正常协作

**正确代码**:
```typescript
async send(target: string, message: string, options?: SendOptions): Promise<void> {
  // 只有reply时才剥离，主动send保留mention
  let cleaned = message
  if (options?.replyTo) {
    cleaned = this.stripBlockedMentions(message)
  }
  // ...
}
```

**原理**:
- 主动send → 需要@人协作 → 保留mention
- reply时 → 防止触发对方bot循环 → 剥离目标bot的mention

## Bot ID参考

| Bot | Discord ID |
|-----|-----------|
| CC Bot | `1504373837880627280` |
| 小柯 (Hermes) | `1502967020550098984` |
| TestEngine | `1509036814885978115` |
| 姐姐 (OpenClaw) | `1502999996616933428` |

## 🔴 stripMentionIds改了还是循环（21:35事件）

CC按小柯方案改了 `stripMentionIds` 只在reply时剥离，但TestEngine和CC还是循环了。

**根本原因**：stripMentionIds只管出站mention文本，但如果对方bot监听频道所有消息（不是只监听@mention），剥掉mention文本也没用——对方看到消息就回复。

**结论**：防循环需要**双方配合**：
- TestEngine侧：stripMentionIds剥CC的mention（只reply时）✅
- CC侧：要么 `requireMention: true`（只回应被@的消息），要么也加stripMentionIds剥TestEngine的mention
- 如果对方不改，只能杀进程

## TestEngine进程管理

CC的cc-connect会自动重启TestEngine，杀了进程会立刻拉起新的。要彻底停TestEngine：
1. 杀TestEngine的tsx进程（多个node子进程）
2. 同时杀CC的cc-connect进程
3. 或者让CC手动停

PowerShell杀TestEngine：
```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*tsx*main.ts*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

## 小柯的血泪教训

- at了TestEngine一次 → 她回复 → 我又回复 → 她又回复 → 互道晚安20条
- **规则**：没有实质性回复就别回复，还停不下来就把对方ID加到Hermes `DISCORD_REPLY_MUTE_BOTS`
- 翀哥连续纠正4次才改对：①allowBots不能改false ②不能把自己加ignoreUserIds ③入站不能屏蔽 ④stripMentionIds只在reply时剥离
