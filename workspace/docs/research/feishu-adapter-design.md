# 飞书通道适配器（FeishuAdapter）设计文档

**作者：** 张小柯  
**日期：** 2026-06-09  
**状态：** 待Review（翀哥 + TestEngine）

---

## 1. 背景

翀哥决定将飞书通道接入Engine（「栖」），优先级高于微信。原因：
- OpenClaw已有bot_bridge.py飞书对接经验，群ID和open_id现成
- 三人飞书群（翀哥+小柯+娘）4/25就想建，内容创作协作需要
- 飞书API规范、webhook/event机制成熟，比微信好对接

## 2. Engine通道注册机制分析

### 2.1 ChannelAdapter接口

所有通道适配器实现`ChannelAdapter`接口（`channels/types.ts`）：

```typescript
interface ChannelAdapter {
  readonly name: string           // 'discord' | 'feishu' | ...
  connect(): Promise<void>        // 建立连接
  disconnect(): Promise<void>     // 断开连接
  send(target, message, options?)  // 发消息
  sendFile?(target, msg, attachment) // 发文件
  startTyping?(channelId)         // typing indicator
  stopTyping?(channelId)
  addReaction?(channelId, msgId, emoji)
  sendPreview?(channelId, content, agentName)  // streaming preview
  editPreview?(handle, content)
  deletePreview?(handle)
  onMessage(handler)              // 注册入站回调
}
```

### 2.2 注册方式

两种注册路径（`channels/manager.ts`）：

1. **loadFromConfig** — 配置文件驱动，自动构建adapter
2. **registerAdapter** — 外部注入已初始化的adapter

当前Discord走loadFromConfig，飞书也一样。

### 2.3 loadFromConfig扩展点

`manager.ts:42-66`：

```typescript
loadFromConfig(config: ChannelConfig): void {
  if (config.discord?.enabled) { /* ... */ }
  // 飞书、企微、Telegram — 后续 Phase  ← 就在这里加
}
```

需要在`ChannelConfig`类型和`loadFromConfig`方法中添加飞书分支。

### 2.4 InboundMessage统一格式

所有通道转成统一格式：
```typescript
interface InboundMessage {
  content: string       // 消息文本
  from: string          // 发送者ID（飞书用 open_id）
  fromName?: string     // 显示名
  target: string        // 目标（群聊用 chat_id，DM 用 open_id）
  channel: string       // 通道名 'feishu'
  isBot?: boolean
  isMentioned?: boolean
  metadata?: Record<string, string>  // 平台特有
  attachments?: InboundAttachment[]
}
```

## 3. 飞书接入方案

### 3.1 技术选型

**SDK：** `@larksuiteoapi/node-sdk`（飞书官方Node.js SDK）
- 自动管理tenant_access_token生命周期
- 结构化API封装（发消息、收事件等）
- 支持长连接（WebSocket）模式，无需公网IP

**消息接收方式：** 长连接（WebSocket）
- 不需要公网webhook地址
- 适合开发/测试环境
- 飞书SDK内置支持

### 3.2 飞书开放平台配置（翀哥操作）

**Step 1：创建应用**
- open.feishu.cn → 创建企业自建应用
- 获取 App ID + App Secret

**Step 2：配置权限**
| 权限 | 标识 | 用途 |
|------|------|------|
| 接收群@消息 | `im:message.group_at_msg` | 群聊@bot触发 |
| 接收私聊消息 | `im:message.p2p_msg` | DM触发 |
| 发送消息 | `im:message:send_as_bot` | bot回复 |
| 上传下载文件 | `im:resource` | 附件处理 |
| 获取用户信息 | `contact:user.base:readonly` | 用户名显示 |

**Step 3：配置事件订阅**
- 订阅 `im.message.receive_v1`（接收消息事件）
- 长连接模式无需配置回调URL

**Step 4：发布应用**
- 版本管理 → 创建版本 → 提交审核

### 3.3 配置文件结构

在`xiaoke.json`（或任意profile配置）中：

```json
{
  "channels": {
    "discord": { ... },
    "feishu": {
      "enabled": true,
      "appId": "cli_xxx",
      "appSecret": "xxx",
      "dmPolicy": "pairing",
      "groupPolicy": "mention-only",
      "feishuUserId": "ou_xxx"
    }
  }
}
```

### 3.4 新增文件

| 文件 | 预估行数 | 职责 |
|------|---------|------|
| `channels/feishu.ts` | ~350行 | FeishuAdapter实现 |
| 其他 | ~50行 | manager.ts配置加载 + 类型定义 |

### 3.5 FeishuAdapter核心设计

```typescript
export interface FeishuConfig {
  appId: string
  appSecret: string
  dmPolicy?: 'pairing' | 'open'
  groupPolicy?: 'open' | 'mention-only'
  feishuUserId?: string   // bot自己的open_id（过滤自身消息）
}

export class FeishuAdapter implements ChannelAdapter {
  readonly name = 'feishu'
  private client: lark.Client
  private wsClient: lark.WSClient  // 长连接
  private config: FeishuConfig

  async connect(): Promise<void> {
    // 1. 初始化 lark.Client（API调用用）
    // 2. 初始化 WSClient（接收事件用）
    // 3. 注册 im.message.receive_v1 事件处理
  }

  async send(target: string, message: string, options?: SendOptions): Promise<void> {
    // target = chat_id（群聊）或 open_id（私聊）
    // 调用 client.im.message.create
    // 支持飞书富文本/卡片格式
    // 处理飞书消息长度限制（按段落拆分）
  }

  private handleFeishuEvent(data): void {
    // 飞书事件 → InboundMessage 转换
    // 过滤自身消息
    // 识别@mention
    // 调用 this.messageHandler
  }
}
```

### 3.6 消息格式映射

| 飞书 | InboundMessage |
|------|---------------|
| `event.sender.sender_id.open_id` | `from` |
| `event.sender.sender_type == 'bot'` | `isBot` |
| `event.message.chat_id` | `target`（群聊） |
| `event.message.chat_type == 'p2p'` | DM判断 |
| `event.message.mention` | `isMentioned` |
| `event.message.content` (JSON) | `content`（需解析飞书富文本JSON） |

### 3.7 关键技术点

**0. 消息去重（TestEngine Review补充）**
飞书事件可能重复投递，需要用 `message_id` 做幂等过滤：
```typescript
private recentMessageIds = new Set<string>()  // 同 DiscordAdapter
// 收到事件时先检查 message_id 是否已处理过
// 定期清理（保留最近5分钟的ID）
```

**1. 消息内容解析**
飞书消息体是JSON字符串，不同msg_type格式不同：
```json
// text类型
{"text": "hello"}
// post类型（富文本）
{"title":"标题","content":[[{"tag":"text","text":"内容"}]]}
```
需要统一提取纯文本给Engine。

**1.1 @mention文本剥离（TestEngine Review补充）**
飞书@mention在文本中是 `@_user_1` 这样的占位符，传给LLM前需要清掉：
```typescript
content = content.replace(/@_user_\d+/g, '').trim()
```

**2. 消息发送格式**
建议用`interactive`（卡片消息），支持更丰富的排版。但初期先用`text`类型快速跑通。

**2.1 分段发送的引用关系（TestEngine Review补充）**
长消息需分段发送时，Phase 1连续发即可，但体验可能割裂。后续Phase可以考虑用飞书卡片的多区块/折叠来优化。

**3. 长连接 vs Webhook**
- 长连接：不需要公网IP，开发环境友好
- Webhook：生产环境更稳定
- SDK两种都支持，代码层面只在connect()里不同

**3.1 WSClient重连（TestEngine Review补充）**
SDK内置了自动重连，不需要自己实现。但要监听断连事件打日志：
```typescript
wsClient.on('disconnected', () => console.warn('[feishu] WS disconnected'))
wsClient.on('connected', () => console.log('[feishu] WS connected'))
```

**3.2 Webhook模式预留（TestEngine Review补充）**
配置文件里预留 `encrypt_key` 和 `verification_token` 字段，后续切webhook模式时不用改配置结构：
```json
{
  "feishu": {
    "enabled": true,
    "appId": "...",
    "appSecret": "...",
    "mode": "ws",
    "encryptKey": "",
    "verificationToken": ""
  }
}
```

**4. 消息长度限制**
飞书单条消息有长度限制（文本30KB，卡片约更短），需要像Discord一样做分段发送。

**5. Typing Indicator**
飞书没有原生typing indicator API，这个功能可以不实现（标记为可选）。

**6. Reaction**
飞书支持消息表情回复（`im.message.reaction` API），可以对齐Discord的reaction机制。

**7. 多Profile共存（TestEngine Review补充）**
同一个飞书appId不能被两个profile同时连接——SDK会冲突。如果未来多个profile都要用飞书，需要每个profile创建独立的飞书应用，或者在Engine层做消息路由分发（一个飞书连接，按群/用户路由到不同profile）。

## 4. 实施计划

### Phase 1：最小可用（目标1晚）
- [ ] `channels/feishu.ts` 核心实现
- [ ] connect/disconnect/send 三个必须方法
- [ ] 飞书事件 → InboundMessage 转换
- [ ] manager.ts 加载飞书配置
- [ ] 配置文件加 feishu 字段
- [ ] 基本DM和群聊@bot消息收发

### Phase 2：体验完善
- [ ] 富文本消息解析（post/at等格式）
- [ ] 卡片消息发送（更好看的回复）
- [ ] 附件收发（图片/文件）
- [ ] Reaction支持

### Phase 3：生产就绪
- [ ] Webhook模式支持（生产环境）
- [ ] 飞书群管理（创建群、拉人）
- [ ] Streaming preview适配

## 5. 依赖

- `@larksuiteoapi/node-sdk` — 飞书官方SDK
- 飞书开放平台企业自建应用（App ID + App Secret）
- 翀哥在飞书后台完成权限配置和应用审核

## 6. 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| 飞书应用审核需要时间 | Phase 1可能被阻塞 | 先用测试环境开发 |
| 长连接稳定性 | 开发环境可能有断连 | 加自动重连逻辑 |
| 消息格式解析复杂 | 富文本/at/图片混合消息解析 | Phase 1只支持纯文本 |
| 飞书SDK版本更新 | API变化 | 锁定版本号 |

## 7. 待确认

- [ ] App ID + App Secret（等娘回复）
- [ ] 飞书应用是否已创建？还是需要新建？
- [ ] 三人群（翀哥+小柯+娘）是否已存在？chat_id？
- [ ] 先用长连接还是直接上webhook？
