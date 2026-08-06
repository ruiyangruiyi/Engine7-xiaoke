---
name: 消息元数据注入
description: Engine消息元数据注入到LLM上下文的完整方案：InboundMeta对象透传，三层命名分离，支持多平台扩展
type: reference
keywords: [元数据, InboundMeta, prompt, 通道, 多平台, discord, feishu]
created: 2026-06-09
updated: 2026-06-10T08:00
---

## 背景

6/9凌晨小柯跟TestEngine循环回复，但看不到发送者ID，分不清是谁在说话。翀哥要求把消息元数据注入到LLM的上下文里。

## 删改演进过程（完整记录）

### 起因

6/9凌晨小柯跟TestEngine循环回复，看不到发送者ID，猜错屏蔽对象。翀哥说"明天先搞元数据这个事，再搞飞书"。

### 问题根因

`engine-startup.ts:1269`，`submitMessage()`调用时InboundMessage的`from`/`fromName`被丢了——只传了`channel`和`target`。全链路溯源：
- adapter层InboundMessage有完整信息（from/fromName/target/channel/metadata）
- engine-startup的submitMessage只取channel和target，其余丢弃
- handleQuery/buidDynamicPrompt根本不知道谁在说话

### v1（senderId/senderName）：最小可行版，5个文件各加几行

```
submitMessage({ ..., senderId: inbound.from, senderName: inbound.fromName })
→ QueuedMessage.senderId/senderName
→ handleQuery(... senderId, senderName)
→ buildDynamicPrompt({ senderId, senderName })
→ prompt输出"发送者ID: xxx"
```

TestEngine独立分析得出完全一致的路径和注入点，双review通过。

### v2 通用性扩展：翀哥质疑"飞书/微信怎么办？"

翀哥原话："有没有考虑到通用性？比如接到飞书或者微信，所以还有source（来源）+ 私信/频道 + 发送者id + 发送者名字 + 发送时间 + TestEngine"

补充字段：
- `channelType?: 'dm' | 'group'` — 消息类型（DiscordAdapter用guild判断填充）
- `messageId` — 平台消息ID
- `channel` — 来源通道名（discord/feishu/weixin，已有）

### v3 inboundMeta对象重构：TestEngine指出散字段透传很蠢

TestEngine原话："InboundMessage 层不动 — from/target/channel 跟平台概念对齐。内部透传层统一用 InboundMessage 的命名。msg_send 层保持 to/channel_id/source。"

"让 handleQuery 直接接受 inbound: InboundMessage，中间层不拆字段。现在逐个字段拆开透传，每加一个字段要改 5 个文件，非常蠢。"

**重构**：把散字段合成为一个`inboundMeta`对象。之前每加一个字段改5处，现在中间层零改动。

```typescript
// 之前（散字段）
submitMessage({ channelName: ..., channelTarget: ..., senderId: ..., senderName: ..., channelType: ... })

// 之后（对象透传）
submitMessage({ inboundMeta: inbound })
```

### v3.1 命名三层体系+优化

翀哥质疑"字段名在代码里是什么？不要有歧义"，参考msg_send/media_send的参数命名风格后，TestEngine系统梳理了三层命名：

| 层 | 命名 | 语义 | 例子 |
|---|---|---|---|
| adapter层（InboundMessage） | `from` / `channel_id` / `channel` | 入站 — 别人发给我 | Discord/飞书adapter填充 |
| 透传层（InboundMeta） | 同adapter层 | 直接从InboundMessage赋值 | 中间层不映射不改名 |
| 工具层（msg_send） | `to` / `channel_id` / `source` | 出站 — 我发给别人 | 方向相反，`channel_id`入站出站统一 |

`from`和`to`方向相反，强行统一反而混淆。但`channel_id`入站出站是同一个东西，已统一命名（6/11凌晨将入站`target`改为`channel_id`，消除歧义）。

优化建议（TestEngine提出，已采纳）：
1. `engine-startup.ts` 直接 `inboundMeta: inbound`（InboundMessage是InboundMeta超集）
2. `prompt.ts` import InboundMeta复用，不重复定义

---

## 最终方案

**7个文件，新增InboundMeta对象，中间层只传对象不感知字段。**

### 新增类型：InboundMeta（message-queue.ts）

```typescript
export interface InboundMeta {
  from: string           // 发送者ID
  fromName?: string      // 发送者显示名
  channel: string        // 来源通道（discord/feishu/weixin）
  channelType?: 'dm' | 'group'  // 消息类型
  channel_id?: string    // 频道ID（群聊）或对方ID（DM），入站出站统一命名
  messageId?: string     // 平台消息ID
}
```

### 透传链

```
InboundMessage（adapter层，各平台填充）
  → engine-startup: submitMessage({ inboundMeta: inbound })  ← 直接赋值，InboundMessage是InboundMeta超集
    → QueuedMessage.inboundMeta（中间层透传，不感知字段）
      → handleQuery(... inboundMeta)
        → buildDynamicPrompt({ inboundMeta })
          → prompt"运行时上下文"section输出
```

### 改动文件清单

| 文件 | 改动 |
|------|------|
| `channels/types.ts` | InboundMessage加 `channelType?` + `messageId?` |
| `channels/discord.ts` | DiscordAdapter填充 `channelType`（guild判断）+ `messageId`（msg.id） |
| `core/message-queue.ts` | 新增 `InboundMeta` 接口，QueuedMessage加 `inboundMeta?` |
| `core/message-dispatcher.ts` | SubmitMessageParams加 `inboundMeta?`，透传到enqueue和handleQuery |
| `handle-query.ts` | handleQuery/handleQueryInner加 `inboundMeta?` 参数，传给buildDynamicPrompt |
| `prompt.ts` | DynamicPromptOptions加 `inboundMeta?`，运行时上下文输出完整元数据 |
| `engine-startup.ts` | submitMessage时 `inboundMeta: inbound` 直接赋值 |

### v4（6/17 翀哥拍板——user消息头meta格式带channelID）

翀哥测试后发现原meta头缺频道信息——光看`[meta: discord/601669300343799819 (sleepyzhang)]`分不清是群聊还是DM、不知道在哪个频道。

6/17晚三次迭代后最终定稿（姐姐提的`#@`方案，翀哥确认）：
```
群聊: [meta: discord#1504385800366854234@601669300343799819 (sleepyzhang)]   ← #频道 @ID
DM:   [meta: discord@601669300343799819 (sleepyzhang)]                       ← 纯@无#
```

**区别：** 群聊带`#channelID`，DM无`#`。扫一眼能分清是群聊还是DM。

**✅ 翀哥+姐姐意见一致，已确认上线。**

### prompt输出格式（system prompt末尾的运行时上下文保持不变）

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

### 三层命名设计

| 层 | 命名 | 语义 | 例子 |
|---|---|---|---|
| adapter层（InboundMessage） | `from` / `channel_id` / `channel` | 入站 — 别人发给我 | Discord/飞书adapter填充 |
| 透传层（InboundMeta） | 同adapter层 | 直接从InboundMessage赋值 | 中间层不映射不改名 |
| 工具层（msg_send） | `to` / `channel_id` / `source` | 出站 — 我发给别人 | `from→to`方向相反，`channel_id`入站出站统一 |

`from`和`to`方向相反，强行统一成一个名字反而混淆。但`channel_id`入站出站是同一个东西，已统一命名（6/11凌晨将入站`target`改为`channel_id`，消除歧义）。

### 扩展性

以后加新字段（如飞书的`chat_id`、微信的`corp_id`）：
1. InboundMessage加字段
2. 对应adapter填充
3. prompt.ts的meta输出加一行

中间层（queue/dispatcher/handle-query）零改动。

非user来源（inbox/heartbeat/cron）不传inboundMeta，因为是系统消息。

### 验证（6/10实测通过）

翀哥在CC频道发"看下我是谁 哪个通道给你的"，小柯正确识别：
- 来源：discord
- 消息类型：群聊
- 频道ID：1504385800366854234
- 发送者ID：601669300343799819
- 发送者名称：sleepyzhang

后续翀哥切换频道（CC→客厅：`1503034906081624174`），小柯正确检测到频道变化。元数据注入已验证通过。

**注入位置确认**（翀哥追问"每个turn都会有么"后确认）：
- **不在** system prompt的stable部分
- **在** `buildDynamicPrompt`的"运行时上下文"section
- **仅用户消息触发**（`handleQueryInner`调用一次），tool call循环不重建
- `inboundMeta`为空时整段不输出（系统消息如inbox/heartbeat/cron）
- 翀哥明确："这样是对的 OK 这样不会浪费上下文"

注意：元数据注入到LLM的prompt里，**不会发到频道里**，用户看不到。

#### 频道切换验证

翀哥从CC频道（`1504385800366854234`）切到客厅（`1503034906081624174`）发消息，小柯正确检测到频道ID变化——per-turn重建生效。

### Review记录

- TestEngine三轮review全部通过
- 翀哥review通过
- 优化建议已采纳：`inboundMeta: inbound`直接赋值、import复用InboundMeta类型

### 提交记录

- commit `c8063b0` — feat: 消息元数据注入LLM上下文 (InboundMeta)，已推送
- 改动文件清单：channels/types.ts, channels/discord.ts, core/message-queue.ts, core/message-dispatcher.ts, handle-query.ts, prompt.ts, engine-startup.ts

### CC（OpenClaw侧）同样看不到元数据

6/10验证：翀哥让小柯问CC"能不能知道你在哪跟他说话"。CC回复看不到频道ID/发送者ID/来源平台，只能收到纯文字。跟小柯之前完全一样的问题——底层有信息但没注入到上下文。CC那边需要OpenClaw侧做类似改造，跟Engine这边的方案不同（不同的prompt构建体系）。
