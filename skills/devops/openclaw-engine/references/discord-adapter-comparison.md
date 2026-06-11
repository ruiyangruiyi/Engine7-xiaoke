# Discord Adapter: CC vs Hermes 对比分析 (2026-05-27)

CC `channels/discord.ts` (193行) vs Hermes `gateway/platforms/discord.py` (5009行)。

## 架构一致性 ✅

| 维度 | CC (discord.js) | Hermes (discord.py) |
|------|----------------|---------------------|
| 核心接口 | ChannelAdapter (connect/disconnect/send/onMessage) | BasePlatformAdapter (connect/disconnect/send) |
| 注入模式 | ✅ 外部Client注入 + `ownsClient` | ❌ 无原生注入，但通过gateway runner桥接 |
| 自身消息过滤 | `msg.author.id === client.user.id` | `message.author == self._client.user` |
| bot过滤 | `msg.author.bot && !config.allowBots` | `DISCORD_ALLOW_BOTS` env: none/mentions/all |
| mention检查 | guild级 `requireMention` | 颗粒度更细：channel/thread/guild级别 |
| stripMentions | 正则 `<@!?\d+>` | 同，额外处理 `<@!` 变体 |
| send → reply | `options.replyTo` fetch原消息再reply | 同 |
| Partials | ✅ Channel + Message (DM必需) | discord.py不需要 |
| **消息去重** | ✅ `recentMessageIds` Set (500/250裁剪) | `MessageDeduplicator` |
| **多Agent过滤** | ✅ mentionedBots + isMentioned检查 | 同 |
| **消息分段** | ✅ `splitMessage()` 按换行/空格/硬切 | `_SPLIT_THRESHOLD=1900` |
| **出站mention剥离** | ✅ `stripBlockedMentions()` + `stripMentionIds` | `DISCORD_REPLY_MUTE_BOTS` |
| **统一filter出口** | ✅ `MessageFilter` 接口 + `ChannelManager.handleInbound()` | 无统一filter接口 |

## 关键踩坑教训

### ⚠️ Bot屏蔽：出站剥离 ≠ 入站忽略

CC曾把bot屏蔽做成**入站拦截**（`ignoredUserIds`直接跳过CC消息），导致：
- CC发的东西engine根本看不到 → 无法干活
- CC作为工具人派活给engine，engine却听不见

**正确做法**（翀哥纠正）：
- CC消息正常收、正常处理
- **回复时**用 `stripBlockedMentions()` 把CC的 `<@ID>` 从回复内容里剥离
- 避免形成 CC → engine → @CC → CC触发 → engine → ... 的循环对话

跟OpenClaw的 `CC_REPLY_BLOCK` 是同一个逻辑——**出站拦截**。

### ⚠️ 统一filter出口 > 每个adapter各自过滤

翀哥指出：bot屏蔽不只discord的事，飞书/微信/企微都需要。所以：
- `MessageFilter` 接口放在 `channels/types.ts`（平台无关）
- `ChannelManager.handleInbound()` 统一过filter链
- 未来加新通道（飞书/企微）零成本 — adapter正确构造 `InboundMessage`，屏蔽自动生效
- Discord特有的逻辑（mention过滤、guild requireMention）仍留在 `DiscordAdapter.handleMessage()`

### 🔴 main.ts assistant消息重复推入Bug

```typescript
// L148-151 — 🐛 msg.assistant() 推了两遍
history.push(msg.user(text))
history.push(...toolHistoryEntries)
history.push(msg.assistant(fullResponse))
history.push(msg.assistant(fullResponse))  // ← 重复！
```

后果：跑几轮后history膨胀，模型看到自己说了两遍同样的话。
修法：删掉一行。

## CC已修的特性 ✅ (2026-05-27 第二轮review)

| 特性 | 状态 | 实现方式 |
|------|------|----------|
| 消息去重 | ✅ | `recentMessageIds` Set, >500裁剪到250 |
| 多Agent共存过滤 | ✅ | guild消息里检查 `mentionedBots` + `isMentioned` |
| 消息分段 | ✅ | `splitMessage()` 2000字符限制, 按换行→空格→硬切 |
| 出站mention剥离 | ✅ | `stripBlockedMentions()` + `DiscordConfig.stripMentionIds` |
| 统一filter出口 | ✅ | `MessageFilter` 接口 + `ChannelManager.addFilter()` |

## CC仍缺失的特性（框架阶段不急）

| 特性 | 优先级 | 说明 |
|------|--------|------|
| Allowed Users白名单 | 🟡 | 框架独立跑时的安全边界 |
| 频道白名单/黑名单 | ⚪ | allowed_channels / ignored_channels |
| Auto-thread | ⚪ | 上层（engine/集成方）的责任 |
| 附件处理 | ⚪ | InboundMessage没有附件字段，接vision的前置条件 |
| Voice/Slash Commands/Forum | ⚪ | 薄通道层不需要 |

## Hermes的三层消息反馈机制（CC需要学习的）

翀哥看到engine at TestEngine时只有"正在输入..."一个反馈，不满意。Hermes有三层：

### 第一层：ACK确认（收到即回复）
收到用户消息时，如果正在忙，**立即发一条状态消息**：
- `⚡ Interrupting current task (2 min elapsed, iteration 3/90, running: web_search). I'll respond to your message shortly.`
- `⏳ Queued for the next turn (running: terminal). I'll respond once the current task finishes.`
- 关键信息：正在干什么、进度、预计多久
- 30秒去重，用户连发多条不刷屏
- 代码：`gateway/run.py` L2397-2447, `HERMES_GATEWAY_BUSY_ACK_ENABLED` 控制

### 第二层：状态更新（每阶段更新）
- Hermes用 `sendStatus()` + 临时消息实现
- 每个阶段发一条状态消息（"💭 思考中..."→"🔧 web_search"→"✍️ 生成中"）
- 进入下一阶段时删掉上一条状态消息
- 最终回复发完后最后一条状态也删掉 → 聊天记录干干净净

### 第三层：持续typing循环
- Hermes `send_typing()` (L2681-2713)：启动后台asyncio task，每8秒POST `/channels/{id}/typing`
- Discord的typing indicator只持续~10秒，单次调用10秒后就断了
- 用 `stop_typing()` 取消后台task
- 还有 `pause_typing_for_chat()` / `resume_typing_for_chat()` 暂停/恢复
- CC现在的 `sendTyping()` 只调一次，LLM推理>10秒就断了

### CC应该怎么加
建议实现方式（推荐**临时状态消息**）：
```typescript
// DiscordAdapter 新增
private _statusMsgIds = new Map<string, string>()

async sendStatus(channelId: string, status: ProcessingStatus): Promise<void> {
  // 删上一条状态 → 发新的状态消息 → 存ID
  // 'done'阶段删掉最后一条
}

// 替换 sendTyping() 为持续循环
startTyping(channelId: string): void   // 每8秒刷一次
stopTyping(channelId: string): void    // 清interval
pauseTyping(channelId: string): void   // tool执行中间暂停
resumeTyping(channelId: string): void  // 恢复
```

## Hermes的成熟实践（CC可借鉴的代码模式）

### connect() 安全措施
```python
# Hermes在connect时做了：
1. 平台锁 (acquire_platform_lock) — 防止多实例同时连
2. Opus codec加载 — voice前置条件
3. proxy解析 (DISCORD_PROXY / 系统代理)
4. 旧Client清理 — 重连前先close之前的client防zombie websocket
5. allowed_mentions — 默认禁@everyone/roles，防LLM输出炸群
6. ready事件等待 — on_message在ready之前block
```

### on_message 过滤链
```
Hermes的完整过滤链（按顺序）：
1. ready事件等待（timeout 30s）
2. dedup去重
3. 忽略自身消息
4. 忽略系统消息（thread rename, pin, member join等）
5. bot过滤 (DISCORD_ALLOW_BOTS)
6. 用户白名单 (DISCORD_ALLOWED_USERS + ROLES)
7. 多Agent共存过滤（@了其他bot但没@自己→跳过）
8. → _handle_message()
```

### _handle_message 路由逻辑
```
1. mention-stripped content保存
2. allowed_channels 检查
3. ignored_channels 检查
4. free_response_channels 检查
5. voice-linked channel 检查
6. bot_thread 检查（之前参与过的thread不需要mention）
7. auto-thread 创建
8. 消息类型判断 (TEXT/PHOTO/VIDEO/AUDIO/DOCUMENT/COMMAND)
9. 构建source元数据 (chat_id, thread_id, guild_id, message_id)
10. 附件下载到本地cache
11. → 回调到gateway runner
```
