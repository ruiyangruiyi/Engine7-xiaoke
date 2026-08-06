# TestEngine 回复功能三层断裂分析 (2026-05-27)

## 问题
TestEngine能收到消息、能发消息，但发的不是"回复"格式（Discord的reply thread），而是一条普通消息。用户看不到上下文关联。

## 根因：三层断裂

### 第1层：ChannelManager.send() 不传 options
```typescript
// manager.ts:100
async send(channelName: string, target: string, message: string): Promise<void>
```
签名没有 `options` 参数，`replyTo` 永远到不了 DiscordAdapter。

### 第2层：main.ts 调用时不传 messageId
```typescript
// main.ts:442
channelManager.send(inbound.channel, inbound.target, toSend)
// inbound.metadata.messageId 有值但 send() 不接受
```

### 第3层：DiscordAdapter.send() 有 replyTo 逻辑但无人调用
```typescript
// discord.ts:89-94 — 写了但没用到的死代码
if (options?.replyTo && i === 0) {
    const origMsg = await channel.messages.fetch(options.replyTo)
    await origMsg.reply(chunks[0])
    continue
}
```

### 配置白配
`engine-config.json` 里 `"replyToMode": "all"` 没被任何代码读取。

## 修复方案

1. **ChannelManager.send() 加 options：**
```typescript
async send(
  channelName: string, target: string, message: string,
  options?: { replyTo?: string }
): Promise<void> {
  const adapter = this.adapters.find(a => a.name === channelName)
  if (!adapter) return
  await adapter.send(target, message, options)
}
```

2. **main.ts 流式回复第一条用 replyTo：**
```typescript
let firstReply = true
onText: (text) => {
  streamBuffer += text
  if (shouldFlush) {
    const toSend = streamBuffer
    streamBuffer = ''
    const opts = firstReply && messageId ? { replyTo: messageId } : undefined
    firstReply = false
    channelManager.send(inbound.channel, inbound.target, toSend, opts).catch(() => {})
  }
}
```

3. **检查 types.ts ChannelAdapter.send() 签名** — 确保接口也接受 options

4. **读取 replyToMode 配置** — 在 handleMessage 或 main.ts 里根据配置决定是否自动 replyTo

## 状态
- 🔴 待修（已通知CC，@CC用 `<@1504373837880627280>`）
