# 消息元数据注入 — 技术文档

**日期：** 2026-06-09
**状态：** 已完成并验证通过（6/10）
**commit：** `c8063b0`

---

## 问题

小柯收到用户消息时看不到发送者ID、频道ID等元数据，无法区分谁在说话。6/9凌晨跟TestEngine循环回复时暴露。

## 方案演进

### V1：散字段透传（已废弃）
最初把senderId/senderName/channelType/messageId拆成4个独立字段逐层透传。每加一个字段要改5个文件（queue→dispatcher→handleQuery→prompt→startup）。

### V2：InboundMeta对象透传（最终方案，TestEngine建议）
把散字段合成一个`InboundMeta`对象，中间层只传对象不感知字段。以后加新字段只改InboundMessage + prompt.ts两处。

## 核心设计

### InboundMeta类型

定义在 `core/message-queue.ts`：

```typescript
export interface InboundMeta {
  from: string           // 发送者ID（Discord user ID / 飞书 open_id）
  fromName?: string      // 发送者显示名
  channel: string        // 来源通道（discord/feishu/weixin）
  channelType?: 'dm' | 'group'  // 私信还是群聊
  target?: string        // 频道ID（群聊）或对方ID（DM）
  messageId?: string     // 平台消息ID
}
```

### 透传链

```
InboundMessage (adapter层，各平台填充)
  ↓
engine-startup.ts: submitMessage({ inboundMeta: inbound })  ← 直接赋值
  ↓
QueuedMessage.inboundMeta (中间层透传)
  ↓
handleQuery(... inboundMeta)
  ↓
buildDynamicPrompt({ inboundMeta })
  ↓
prompt "运行时上下文" section → LLM看到完整元数据
```

### InboundMessage扩展（channels/types.ts）

新增两个字段：
- `channelType?: 'dm' | 'group'` — 消息类型
- `messageId?: string` — 平台消息ID

### DiscordAdapter填充（channels/discord.ts）

```typescript
const inbound: InboundMessage = {
  // ... 原有字段
  channelType: msg.guild ? 'group' : 'dm',  // 有guild就是群聊
  messageId: msg.id,                         // Discord消息ID
}
```

### prompt输出（prompt.ts）

```
# 运行时上下文
当前时间: 2026/6/9 08:30:00
平台: unknown
来源: discord
消息类型: 群聊
频道ID: 1504385800366854234
发送者ID: 601669300343799819
发送者名称: 翀哥
消息ID: 1234567890
会话ID: xxx-uuid
```

## 三层命名设计

| 层 | 命名风格 | 语义 | 说明 |
|---|---|---|---|
| adapter层（InboundMessage） | `from`/`target`/`channel` | 入站 | Discord/飞书adapter写起来自然 |
| 透传层（InboundMeta） | 同adapter层 | 传递 | 直接赋值不映射，零认知负担 |
| 工具层（msg_send） | `to`/`channel_id`/`source` | 出站 | 方向相反，不强行统一 |

## 改动文件清单

| 文件 | 行数变化 | 改动内容 |
|------|---------|---------|
| `channels/types.ts` | +5行 | InboundMessage加channelType/messageId |
| `channels/discord.ts` | +2行 | DiscordAdapter填充新字段 |
| `core/message-queue.ts` | +12行 | 新增InboundMeta接口，QueuedMessage加inboundMeta |
| `core/message-dispatcher.ts` | +3行 | SubmitMessageParams加inboundMeta，透传 |
| `handle-query.ts` | ~0行 | handleQuery加inboundMeta参数替代散字段 |
| `prompt.ts` | +15行 | buildDynamicPrompt从inboundMeta输出元数据 |
| `engine-startup.ts` | +1行 | submitMessage加 `inboundMeta: inbound` |

## 扩展飞书/微信

1. 飞书adapter填充InboundMessage（from=open_id, channel='feishu', channelType, messageId）
2. 透传层零改动（inboundMeta对象自动携带）
3. prompt自动输出正确格式

## 后续优化

1. **每turn注入浪费** — 同session里from/channel基本不变，只有messageId变化。可以首轮全量注入，后续只更新messageId。当前先全量跑通。
2. **msg_send/media_send加source** — 出站路由需要source字段路由到正确adapter，跟入站元数据是两回事，单独做。
