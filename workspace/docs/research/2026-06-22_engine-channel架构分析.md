# Engine Channel 架构分析

> 日期：2026-06-22 | 作者：小柯 | 目的：为 OAC 嵌入 engine 方案提供依据

## 1. Channel 架构总览

Engine 有 3 个 channel adapter，都实现 `ChannelAdapter` 接口：

```
Discord Adapter  ──┐
Feishu Adapter  ───┤──→ ChannelManager ──→ MessageDispatcher ──→ QueryEngine ──→ LLM
Wechat Adapter  ───┘                                                      │
                                                                          ▼
                                                                    LLM 回复
                                                                          │
                    ┌───────────────────────────────────────────────────┘
                    ▼
              ChannelManager.send(channel, target, message)
```

**所有 channel 都是文本 in / 文本 out**：
- 入站：平台消息 → `InboundMessage` → `MessageDispatcher` → `QueryEngine`
- 出站：LLM 回复 → `ChannelManager.send()` → 平台 API

## 2. ChannelAdapter 接口

`src/channels/types.ts:118-167`：

```typescript
interface ChannelAdapter {
  readonly name: string           // 'discord' | 'feishu' | 'weixin'
  connect(): Promise<void>        // 建立连接
  disconnect(): Promise<void>     // 断开
  send(target, message, options?): Promise<void>  // 发消息
  sendFile?(target, message, attachment): Promise<void>  // 发媒体
  onMessage(handler): void        // 注册入站回调
  // 可选: typing, reaction, preview, slash commands
}
```

**关键**：接口只管文本。没有音频/视频/流式 API。

## 3. 消息流转全链路

### 入站（用户 → LLM）
```
平台事件 (Discord message / Feishu ws / WeChat API)
    │
    ▼
Adapter (discord.ts / feishu.ts / wechat.ts)
    │ 转成 InboundMessage { content, from, channel_id, channel, channelType }
    ▼
ChannelManager.handleInbound()  (manager.ts:143)
    │ 1. 过滤（MessageFilter）
    │ 2. 文本命令拦截（/stop /model 等）
    │ 3. 通过 → messageHandler
    ▼
MessageDispatcher.enqueue()  (dispatcher)
    │ 按 session 路由 + 排队
    ▼
QueryEngine.query()
    │ system prompt + messages → LLM stream
    ▼
LLM 回复
```

### 出站（LLM → 用户）
```
QueryEngine stream chunk
    │
    ▼
engine-startup.ts 的 stream handler
    │ 积累 text → channelManager.send()
    ▼
ChannelManager.send(channel, target, message)
    │
    ▼
Adapter.send(target, message)
    │ 调平台 API
    ▼
用户看到消息
```

## 4. ChannelManager 注册方式

两种（`manager.ts:34-38, 46-117`）：

### 方式 A：loadFromConfig（从配置文件）
```typescript
// manager.ts:46
loadFromConfig(config: ChannelConfig): void {
  if (config.discord?.enabled) { ... new DiscordAdapter(...) }
  if (config.feishu?.enabled) { ... new FeishuAdapter(...) }
  if (config.wechat?.enabled) { ... new WechatAdapter(...) }
}
```

### 方式 B：registerAdapter（注入外部 adapter）
```typescript
// manager.ts:35
registerAdapter(adapter: ChannelAdapter): void {
  this.adapters.push(adapter)
}
```

**方式 B 更灵活**——不需要改 `loadFromConfig`，只需要 `implements ChannelAdapter` 就能注入。

## 5. 新增 Channel 需要改什么

### 5.1 如果是标准文本 channel
1. 写 `src/channels/oac.ts` 实现 `ChannelAdapter`
2. 在 `manager.ts:loadFromConfig` 加 `if (config.oac?.enabled) { ... }`
3. 配置文件加 `oac` section

### 5.2 如果是非标准 channel（如 OAC 音视频）
**不需要实现 `ChannelAdapter`**——因为 OAC 不是文本 channel。

更合理的方式：
1. Engine 加一个 **HTTP webhook endpoint**（`POST /webhook/oac`）
2. OAC 通过 OC Bridge 的 OcChannelClient 调这个 endpoint
3. Engine 收到 text → 走正常 LLM 流程 → 回 text 给 OAC callback
4. **ChannelManager 完全不需要改**

## 6. 关键发现：Engine 已有 18789 端口

OpenClaw 配置（`~/.openclaw/`）有端口 16888（gateway）。但 OAC 的 OC Bridge 默认连 `localhost:18789`。

**需要确认**：18789 是 OpenClaw 的什么端口？是否已有 webhook handler？

如果 18789 已经有 webhook 路由，**OAC 的 OcChannelClient 可能直接就能接上**——不需要写新代码。

## 7. QueryEngine 消息接口

```typescript
// query.ts
query(messages: Message[]): AsyncGenerator<StreamChunk>
```

StreamChunk 类型：`text` | `tool_call` | `tool_result` | `status` | `error`

**OAC 嵌入时**，OAC 只需要调 engine 的 query（通过 HTTP API），拿 text chunk → TTS → speaker。
