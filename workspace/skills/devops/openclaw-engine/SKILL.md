---
name: openclaw-engine
description: OpenClaw 自研引擎代码库——架构、扩展点、已知问题、review/checklist。TypeScript + ESM + async generator。
version: 0.1.0
created: 2026-05-27
updated: 2026-05-27
triggers:
  - review OpenClaw engine
  - engine代码
  - 自研引擎
  - Phase 3 channel
  - add provider/tool/channel to engine
  - openclaw engine debug
  - multi-profile 多进程
  - engine-startup.ts
  - profile-entry/profile-master
---

# OpenClaw Engine

自研AI agent引擎，替代OpenClaw gateway核心。TypeScript + ESM (Node 22+) + async generator流式设计。

**代码位置**: `C:\Users\24045\.openclaw\engine\` (旧项目目录下，只读！不修改姐姐的workspace)
**源码**: `src/` | **编译输出**: `dist/` | **配置**: `openclaw.json`

## 架构概览

```
main.ts (入口: 单Profile CLI + Channel)
  ├── engine-startup.ts    共享引擎启动逻辑（main.ts 和 profile-entry.ts 共用同一份）
  └── core/query.ts        QueryEngine — async generator agent loop

profile-entry.ts (子进程入口: 多Profile模式) → 调用 engine-startup.ts
profile-master.ts (进程管理器: fork/监控/重启/优雅关闭)
main-multi.ts (多Profile入口: 检测profiles[]数组路由)
  ├── models/              LLM Provider层
  │   ├── provider.ts        LLMProvider 接口 + StreamChunk
  │   ├── provider-factory.ts 工厂: openai-completions | anthropic
  │   ├── openai-provider.ts  OpenAI兼容 (GLM/DeepSeek/MiniMax/Ollama)
  │   └── anthropic-provider.ts Anthropic (Claude/MiniMax-M2.7)
  ├── channels/            通道适配器层 (Phase 3)
  │   ├── types.ts           InboundMessage + ChannelAdapter + MessageFilter + PreviewHandle 接口
  │   ├── manager.ts         ChannelManager 配置加载/启停/路由/filter链/preview代理
  │   ├── stream-preview.ts  StreamPreview 节流器（对齐cc-connect streaming.go）
  │   ├── bot-mute-filter.ts BotMuteFilter 可组合过滤
  │   └── discord.ts         DiscordAdapter (注入模式 + 自建模式 + streaming preview)
  ├── tools/               Tool系统（14个文件，2026-05-27整理完成）
  │   ├── types.ts           Tool/ToolSchema/ToolDefinition 接口
  │   ├── registry.ts        单例注册表
  │   ├── executor.ts        并行/串行执行器
  │   ├── features.ts        Feature开关 → Tool加载映射
  │   ├── edit.ts            编辑文件（Claude Code移植: findActualString+引号规范化+风格保留）
  │   ├── read.ts            读文件（Claude Code移植: BOM检测+设备文件保护+文件信息头）
  │   ├── write.ts           写文件（Claude Code移植: 原子写入+敏感路径保护+simpleDiff）
  │   ├── exec.ts            执行shell命令（Claude Code移植: 危险命令黑名单+isDestructive修复）
  │   ├── grep.ts            文件内容搜索（Claude Code移植: ripgrep+3种输出模式）
  │   ├── glob.ts            文件名搜索（Claude Code移植: glob匹配+修改时间排序）
  │   ├── web-search.ts      网络搜索（CC写的，Tavily API，⚠️需改进）
  │   ├── web-fetch.ts       抓网页内容（CC写的，URL验证+redirect，⚠️htmlToText需换turndown）
  │   ├── memory-search.ts   搜 memory/ + topics/ (纯文本匹配)
  │   └── msg-send.ts        发消息（已接ChannelManager）
  ├── messages/types.ts    Message/ToolCall/msg工厂
  ├── session/              Session持久化 (Phase 4)
  │   ├── writer.ts           SessionWriter — OpenClaw兼容JSONL写入（append-only）
  │   └── reader.ts           SessionReader — JSONL恢复为Message[]
  └── config/loader.ts     openclaw.json 配置加载
```

## 核心数据流

```
用户消息 → ChannelAdapter → InboundMessage → main.ts handleQuery()
  → startTyping(channelId) → 每8s续期
  → QueryEngine.query(messages, signal, context) → async generator loop:
    → provider.streamChat() → StreamChunk (text/tool_call/thinking/error)
    → tool_call → pauseTyping → executeTools(context) → registry.get() → handler(args, ctx)
      → ctx.channelManager.send() → ChannelAdapter → 平台
    → tool_result → resumeTyping → 回传LLM → 继续循环
  → 完整回复 → ChannelAdapter.send() → 平台
  → finally: stopTyping(channelId)
```

## 关键接口

### LLMProvider (`models/provider.ts`)
- `formatMessages(systemPrompt, messages)` — 格式化差异
- `streamChat(params)` → `AsyncGenerator<StreamChunk>` — 流式对话
- OpenAI: system放messages; Anthropic: system单独传

### ChannelAdapter (`channels/types.ts`)
- `connect()` / `disconnect()` / `send()` / `onMessage()`
- DiscordAdapter支持**注入模式**: 构造函数接受外部discord.js Client, `ownsClient`标记控制生命周期
- 两种运行模式: **桥接模式**(复用Hermes通道,开发快) + **独立模式**(自带adapter直连,通用交付)
- **Streaming preview接口**(对齐cc-connect): `PreviewHandle(channelId+messageId)` + `sendPreview?(channelId, content)` + `editPreview?(handle, content)` + `deletePreview?(handle)`
- **StreamPreview节流器**(`stream-preview.ts`): appendText积累文本按1500ms/30chars节流，finish/discard/freeze管理生命周期，degrade机制保底

### ToolContext (`tools/types.ts`)
- `QueryEngine.query(messages, signal, context)` — context透传到executeTools
- tool handler通过`context.channelManager`访问ChannelManager，实现依赖注入
- `msg_send` handler: `ctx.channelManager?.send("discord", target, content)` → 无channelManager时fallback console.log

### Tool (`tools/types.ts`)
- `name/description/schema/handler` + 可选: `isConcurrencySafe/isReadOnly/isDestructive/interruptBehavior`
- 自注册: 模块加载时调 `registry.register({...})`

## 扩展指南

### 加新Provider
1. 在 `models/` 下新建 `xxx-provider.ts`，实现 `LLMProvider` 接口
2. 在 `provider-factory.ts` 的 switch 加 case
3. 在 `config/loader.ts` 的 `ProviderConfig.api` 联合类型加新值
4. `openclaw.json` 的 providers 加配置

### 加新Tool
1. 在 `tools/` 下新建 `xxx.ts`，调 `registry.register({...})`
2. 在 `tools/features.ts` 的 `builtInFeatures` 加映射（如果需要feature开关）
3. `main.ts` 加 import（或通过 setupFeatures 动态加载）

### 加新Channel
1. 在 `channels/` 下新建 `xxx.ts`，实现 `ChannelAdapter`
2. 在 `channels/manager.ts` 的 `loadFromConfig()` 加配置解析
3. 配置 openclaw.json 的 channels 字段

## 已知问题 (as of 2026-05-27)

### 已修 ✅
1. ~~main.ts history缺tool交互~~ — Fix2: QueryEngine yield `history` chunk，handleQuery收集assistant(toolCalls)+toolResults存进sessionHistories
2. ~~session无过期清理~~ — Fix3: 5分钟轮询，idle超30分钟的session自动清理（cli session除外）
5. ~~channelsConfig重复读文件~~ — Fix4: EngineConfig加channels字段，main.ts用config.channels不再二次parse
6. ~~Discord DM路径没走cache~~ — Fix1: `client.users.cache.get(target) ?? await fetch()`
7. ~~msg_send还是stub~~ — handler从context.channelManager取ChannelManager，调mgr.send()；无channelManager时fallback console.log

### 需要修的
4. **API key明文** — openclaw.json里zai/zai2/tavily的key都是明文，不支持环境变量覆盖
5. **send()返回void** — 应返回messageId（discord.js的channel.send()返回Message对象，现在浪费了）
6. **🟡 无用户白名单** — 框架独立跑时没有`allowedUsers`安全边界
7. **🔴 无sendAndWait()** — 发消息后无法追踪对方有没有回复。需要：sendAndWait(target, msg, {waitForUserId, timeoutMs}) → Promise<SendResult>，用一次性messageCreate监听器实现，超时返回null
8. **🔴 无消息状态反馈** — 翀哥要求不只是"正在输入..."，要有ACK+状态更新+持续typing三层反馈（详见下方Pitfalls）

### ✅ 已修 (8条code review, 2026-05-27晚)

| # | 问题 | 状态 | 修复 |
|---|------|------|------|
| P0-1 | reader.ts path import在末尾 | ✅ | 移到顶部 |
| P0-2 | read.ts 5MB限制太大 | ✅ | 改为1MB |
| P0-3 | readFileState存content浪费内存 | ✅ | 去掉content只存mtime |
| P0-4 | ~~user消息重复~~ | ❌纠正 | 实际是assistant内容重复，已修(fullResponse→roundText) |
| P0-5 | sessionId格式(discord:xxx) | 设计层 | 按session-mechanism.md方案后续做 |
| P1-6 | 截断砍30%太粗暴 | ✅ | 改为shift最旧1条 |
| P1-7 | text/toolCall互斥导致吞text | ✅ | 去掉互斥判断 |
| P1-8 | flush条件导致重复flush空消息 | ✅ | 改为`if (roundText)` |

### ✅ 已修 (SendOptions回复功能三层断裂, 2026-05-27晚)

1. **manager.ts** — `send()` 加了 `options?: SendOptions` 参数并透传到adapter
2. **main.ts** — 加 `firstReply` 标记，第一条流式回复带 `{ replyTo: messageId }`，后续不带
3. **discord.ts** — 原有replyTo逻辑从死代码变成活代码

### ✅ 已修 (Session恢复最终方案, 2026-05-27晚)

- JSONL文件名用UUID（不用discord_xxx.jsonl）
- **双文件映射**：`platform-map.json`（`discord:userId` → UUID）+ `session-index.json`（UUID → {file, updatedAt}）。内部全用UUID，channel handler入口做一次`getOrCreateSessionId(platformKey)`查找
- JSONL header加engineSessionId字段精确关联
- 重启后续写同一个UUID.jsonl文件（append模式）
- 旧索引自动迁移
- 截断保护：100条/50K tokens/保底10条

### Discord Adapter对比Hermes后发现的缺失 — 全部已修 ✅
5. ~~🔴 消息去重~~ ✅ — `recentMessageIds` Set去重，>500条裁剪到250
6. ~~🔴 多Agent共存过滤~~ ✅ — guild消息检查mentionedBots + isMentioned
7. ~~🟡 send()>2000字会崩~~ ✅ — 超长消息按换行/空格切割多条发送
8. ~~🔴 出站mention剥离~~ ✅ — stripMentionIds + stripBlockedMentions()，send()里自动去掉
9. ~~🟡 sendTyping~~ ✅ — sendTyping(channelId)方法+recvAt时间戳
10. ~~🟡 MessageFilter统一出口~~ ✅ — types.ts MessageFilter接口 + manager.ts filter链

### Phase 3 ✅ (通道层, 2026-05-27完成)
- ChannelAdapter接口 + ChannelManager + DiscordAdapter
- msg_send通过context.channelManager依赖注入
- 双模式: 桥接(注入) + 独立(自建)
- 实测踩坑: MESSAGE CONTENT INTENT、Partials、DM channel ID
- **MessageFilter框架** — 过滤逻辑提到ChannelManager层，adapter只管收发
  - `types.ts` 新增 `MessageFilter` 接口: `shouldIgnore(msg: InboundMessage): boolean`
  - `bot-mute-filter.ts` — BotMuteFilter，可组合的白名单/频率限制基础
  - `manager.ts` — `addFilter(filter)` 注册全局filter链，`handleInbound()` 统一过filter再分发
- **消息去重** — recentMessageIds Set防Discord RESUME重放
- **多Agent共存** — guild消息检查mentions，有@其他bot没@自己→跳过
- **消息分段** — 超2000字符按换行/空格切割
- **出站mention剥离** — `stripMentionIds` + `stripBlockedMentions()` 在send()里去掉指定bot的@mention。⚠️ **必须只在reply时剥离，主动send保留mention**——否则bot间主动@协作也被砍了。改法：`if (options?.replyTo) cleaned = stripBlockedMentions(message)`
- **端到端验证通过** — DM ✅ + 频道(Guild) ✅

### Typing Indicator Lifecycle ✅
- ChannelAdapter接口: `startTyping(channelId)` / `stopTyping(channelId)` / `pauseTyping(channelId)` / `resumeTyping(channelId)`
- DiscordAdapter: `_typingTasks` Map管理每个channel的循环，每8秒续期（Discord typing 10秒过期），pause时跳过续期
- ChannelManager: 4个方法透传到adapter
- main.ts channel loop: 收到消息→startTyping → tool调用时pauseTyping → tool结果回来resumeTyping → 发完回复stopTyping（finally保证清理）
- 生命周期: query开始→start → tool阶段→pause → tool结束→resume → send完成→stop(finally)

### 性能优化 (2026-05-27)
- prompt从33KB缩减到868B（97%压缩），query延迟从12s降到3-5s，总roundtrip从13s降到4-6s（4倍提速）
- 细粒度计时: adapter层recvAt(messageCreate触发时间) + gateway delay(adapter到engine内部处理) + send时间 + total
- Discord send 1-1.3s偏慢（正常应<200ms），可能因channels.fetch()先查后发增加延迟
- 翀哥实测: 日志6.2s但实际等8s，差1.8s是Discord收方向网络延迟(0.5-1s) + 发方向推送延迟(0.5-1s)未计入

### fullResponse→roundText修复 (2026-05-27, CC修)
- main.ts最后一轮`history.push(msg.assistant(fullResponse))`有assistant内容重复bug
- `fullResponse`累积了agent loop所有轮次文字（含中间tool-call轮次），但`toolHistoryEntries`已包含中间轮次assistant消息
- 改成`msg.assistant(roundText)`只推最后一轮文字（roundText在每轮history chunk后清空，只保留当前轮）
- `return fullResponse`不变——完整回复给Discord流式输出用
- **小柯review最初误判为user消息重复**，实际是assistant重复。展开运算符`[...history, x]`创建新数组不修改原引用

### Phase 4 ✅ (Session持久化 + 8个Tool, 2026-05-27)
- **SessionWriter** (`session/writer.ts`) — OpenClaw v5.x兼容JSONL格式
  - session header (type/version/id/timestamp/cwd)
  - message行 (user/assistant/toolResult)，content是ContentBlock数组
  - model_change行、custom_message行
  - genId()用randomBytes(4)，parentId链式追踪
  - append-only写（createWriteStream flags:'a'），每行JSON
- **SessionReader** (`session/reader.ts`) — JSONL恢复为引擎内部Message[]
  - readSessionHeader() 读第一行
  - readSessionHistory() 逐行解析，role:user/assistant/toolResult → SessionMessage[]
  - extractText() 从content数组提取文本
  - listSessions() 按修改时间倒序列出
- **main.ts Session管理** — sessionHistories/sessionWriters/sessionLastUsed三个Map
  - getWriter() 懒创建SessionWriter
  - restoreSession() 预留，暂返回空（TODO: session-id → file映射）
  - 5分钟轮询清理idle超30分钟的session（cli除外）
  - handleQuery()里flushRound()按[assistant, toolResult...]顺序写入JSONL
  - roundText/roundThinking/roundToolCalls/roundToolResults四缓冲区
- **8个Tool** — msg_send + memory_search + read + write + edit + exec + web_search + web_fetch
  - features.ts新增filesystem/shell/webSearch/webFetch四个feature+setup
  - 所有tool遵循registry.register()自注册模式
- **Emoji Reaction反馈** — 👁️已读→✅完成/❌错误，通过ChannelManager.addReaction/removeReaction
- **流式输出到Discord** — 200字+换行切割分段发送，不用等全部回复

### Session Restore (Phase 4续, 2026-05-27) ✅ 完成
- JSONL文件名用UUID（不用平台前缀如discord_xxx.jsonl）
- session-index.json做sessionId→UUID.jsonl映射（跟OpenClaw的sessions.json一致）
- JSONL header加`engineSessionId`字段（如`discord:userId`），重启后精确关联
- 恢复时双重查找：索引 + 扫描JSONL header
- 同一用户多个文件按时间排序合并
- 重启后续写同一个UUID.jsonl文件（append模式）
- 截断保护：RESTORE_MAX_MESSAGES=100，50K token估算上限（3字符≈1token），保底最近10条，超出shift最旧1条
- **Compaction方案已设计**（`references/session-compression-strategy.md`）：4级递进压缩替换粗暴截断——①Smart JSON提取(tool result>8K只保留关键字段,50K→3K) ②旧轮次合并(tool结果折叠进assistant消息) ③截断兜底 ④FIFO原子删除(按完整轮次删)。待实现为 `src/session/compressor.ts`

### Anthropic Provider改进 (2026-05-27)
- anthropic-version从硬编码改成可配置（默认`2025-04-15`，兼容智谱等代理）
- AnthropicProviderConfig加`compatMode`字段
- SSE解析加`message_start`事件处理（含input_tokens usage）
- StreamChunk加`thinking`字段
- Message/StreamChunk加`is_error`字段

### Streaming Event体系 cc-connect对齐Review (2026-05-28, 小柯review)

CC实现了streaming输出对齐cc-connect Event体系，小柯对照`core/engine.go`的`processInteractiveEvents`和`core/message.go`的Event类型做review：
- ✅ EventText/EventToolUse/EventToolResult/EventResult/EventThinking/EventError 六路映射正确
- ✅ result chunk携带content+inputTokens+outputTokens对齐EventResult
- ✅ Reaction机制（👀→✅/❌）一致
- ✅ **Streaming Preview已实现** — 小柯实现，完全对齐cc-connect的streaming.go
- 缺EventPermissionRequest、空result无提示(已修✅)、tool input格式化(已修✅)、缺NO_REPLY、缺auto-compress
- 详见 `references/streaming-event-review-0528.md`

### Streaming Preview ✅ (2026-05-28, 小柯实现)

完全对齐cc-connect的`core/streaming.go`，打字机效果——流式输出实时显示到Discord。

**架构（三层分离）**：

| 层 | 文件 | 职责 |
|---|---|---|
| 接口层 | `channels/types.ts` | `PreviewHandle` + adapter的`sendPreview?/editPreview?/deletePreview?` |
| 管理层 | `channels/manager.ts` | `sendPreview/editPreview/deletePreview` 代理方法 |
| 平台层 | `channels/discord.ts` | send→edit→delete，discord.js `msg.edit()` 实现 |
| 节流器 | `channels/stream-preview.ts`（新，180行） | 节流+生命周期管理，对齐cc-connect的streamPreview struct |
| 接入层 | `main.ts` | onText→appendText, onToolCall→discard, onResult→finish |

**核心类 StreamPreview**（`channels/stream-preview.ts`）：
- `appendText(text)` — 积累文本，按 intervalMs(1500) + minDeltaChars(30) 节流
- `finish(finalText)` — 最终更新preview，返回true=已发/false=需单独发
- `discard()` — 删preview + degrade（tool调用前清preview）
- `freeze()` — 冻结内容（权限请求/中断场景）
- `detachPreview()` — 分离handle让finish不删消息
- **degrade机制** — 任何API失败后静默跳过，不影响正常回复

**Discord preview生命周期**：
1. 首次appendText触发flush → `sendPreview()` 发新消息 → 返回PreviewHandle
2. 后续appendText节流flush → `editPreview()` 用`msg.edit(text)`反复编辑同一条消息
3. tool调用前 → `discard()` → 删preview，发🔧tool指示器
4. response完成 → `finish()` → 最终更新preview为完整内容，或degraded时发新消息

**配置**（`DEFAULT_PREVIEW_CONFIG`）：
- `intervalMs: 800` — 两次编辑最小间隔（⚠️ cc-connect默认1500ms，但智谱等模型输出慢需要更频繁）
- `minDeltaChars: 10` — 最少新增字符才触发编辑（⚠️ cc-connect默认30，但TestEngine每次只吐几个字）
- `maxChars: 2000` — preview最大字符数（Discord消息限制）
- `enabled: true` — 全局开关
- **⚠️ 参数需要按模型调优** — Claude等高速模型可用cc-connect默认值(1500ms/30chars)，智谱/DeepSeek等慢速模型需要更低门槛(800ms/10chars)，否则用户看到"半天输出一个字"

**对齐cc-connect的接口映射**：

| cc-connect (Go) | Engine (TS) |
|------------------|-------------|
| `PreviewStarter.SendPreviewStart()` | `ChannelAdapter.sendPreview()` |
| `MessageUpdater.UpdateMessage()` | `ChannelAdapter.editPreview()` |
| `PreviewCleaner.DeletePreviewMessage()` | `ChannelAdapter.deletePreview()` |
| `streamPreview.appendText()` | `StreamPreview.appendText()` |
| `streamPreview.finish()` | `StreamPreview.finish()` |
| `streamPreview.discard()` | `StreamPreview.discard()` |
| `streamPreview.freeze()` | `StreamPreview.freeze()` |
| `StreamPreviewCfg` | `StreamPreviewConfig` |

- `references/streaming-preview-implementation-0528.md` — Streaming Preview完整实现详解（cc-connect源码对照+Engine 5文件改动+接口映射+效果说明）

### Streaming Preview CC Code Review (2026-05-28, CC review + 小柯修)

CC review了小柯的streaming preview实现，提了5个问题，全部修完：

1. **discard() 是 async 但没被 await（main.ts:649）** — `preview.discard().catch(() => {})` fire-and-forget，如果discard还在删preview消息，紧接着的tool消息可能时序交叉（用户先看到tool消息再看到preview消失）。**修：加 `await`，删完preview再发tool消息。** 这是异步操作时序的经典问题——对Discord这种有API延迟的平台，异步操作之间必须有显式ordering保证。

2. **finish() 超长回复截断丢内容（stream-preview.ts:113）** — 原代码`finalText.length > 2000 ? finalText.slice(0, 1999) + '…' : finalText`，在preview里截断2000字当最终结果。但preview消息被截了内容就不完整。**修：超过2000字直接 `deletePreview + return false`，让上层走 `channelManager.send` 的 `splitMessage` 分段逻辑。** 原则：preview只适合短回复，长回复必须分段发。

3. **editPreview 每次都 fetch 消息（discord.ts:301）** — 打字机效果高频调用（1.5s间隔），每次 `messages.fetch(handle.messageId)` 再 `msg.edit(text)` 浪费一次Discord API。**修：先查 `messages.cache.get(handle.messageId)`，cache有直接edit，没有才fetch。** discord.js会cache已交互过的消息，第二次edit后cache就有数据了。

4. **lastSentAt > 0 语义不精确（stream-preview.ts:84,90）** — 用 `lastSentAt > 0` 判断"是否发过preview"，但如果sendPreview在毫秒级完成，值可能在0附近。**修：改成 `this.previewHandle !== null`，和finish/discard里的判断一致，语义更清晰。**

5. **freeze() 没有调用点** — 当前main.ts没用到freeze()。加了完整注释说明：预留给QueryEngine的interrupt/PermissionRequest机制，未来由/stop或权限确认触发。对齐cc-connect streaming.go的freeze()方法。

**Review教训**：
- async操作在streaming场景必须有显式ordering（await），不能fire-and-forget
- preview的finish()不应截断长文本当最终结果——要么完整更新，要么删掉让分段逻辑处理
- 高频Discord API调用要利用discord.js的cache机制减少请求
- 判断"是否已发过"用显式状态（handle !== null）不用隐式推断（timestamp > 0）

### Streaming Preview 并发Bug修复 (2026-05-28, CC发现+修复)

**现象**：streaming preview开启后，Discord上出现~20条独立消息而不是一条消息反复编辑。

**根因**：`appendText()` 是 sync，调 `flush()` 是 async 但没 await。LLM streaming tokens 到达极快时，第一次 `sendPreview()` 还没 resolve（`previewHandle` 仍 null），后续 flush 也走 sendPreview → 每次都创建新Discord消息。

**CC的修复方案**（`stream-preview.ts`）：
1. 新增 `flushPromise: Promise<void> = Promise.resolve()` — 串行化链
2. `flush()` 改为 `this.flushPromise = this.flushPromise.then(async () => { ... })` — 所有flush操作排队执行
3. `finish()` / `discard()` / `freeze()` 都加 `await this.flushPromise` — 等队列清空再操作
4. 二次检查：`if (displayText === this.lastSentText) return` — 排队期间可能已被前面的flush处理

**原理**：Go用mutex锁串行化，JS用Promise链串行化——殊途同归。`appendText` 不能改成 async（调用方是 sync callback），但内部的 flush 通过 Promise 链保证同一时刻只有一个在执行。

**教训**：sync函数调async方法时，如果async方法有副作用（发消息/改状态），必须串行化。否则快速连续调用会导致状态竞争。

### State-dir目录结构共识 (2026-05-28)

翀哥拍板：Engine运行时根目录叫`state-dir`（跟OpenClaw的`.openclaw/`习惯一致），里面加`workspace/`子目录。测试环境在`D:\testengine\`：
```
D:\testengine\                     ← stateDir（测试环境）
├── agents\main\
│   ├── memory\memory.db            ← memory DB（496MB，4790 chunks）
│   └── sessions\                   ← session JSONL（28个）
├── workspace\                      ← agent工作目录
│   ├── SOUL.md / AGENTS.md
│   ├── memory\                     ← 日记（被 memorySearch 索引）
│   ├── topics\                     ← extraPaths
│   └── docs\                       ← extraPaths
└── logs\engine.log
```
配置：stateDir=D:\testengine, workspace=D:\testengine\workspace

### 测试数据库 (2026-05-28)

姐姐的main.sqlite已拷贝到 `C:\Users\24045\.openclaw\engine\test-data\main.sqlite`（496MB，4790 chunks + bge-m3双写），可随便折腾不动线上的。sqlite-vec 0.1.9已pip安装。

### 文件附件处理 ✅ (6/5, commit 9a9dfb5)

**背景**：TestEngine收到Discord文件附件（txt/docx/pdf等）时，非图片文件直接被丢弃。

**根因**：`engine/src/main.ts:1160` 只过滤了 `image/*` 类型：
```ts
const imageAttachments = inbound.attachments?.filter(a => a.contentType.startsWith('image/'))
```

**CC调研结论**（小柯+翀哥联合分析）：
- CC**不做文件解析/内容注入**
- 下载文件到 `~/.claude/uploads/{sessionId}/`
- 把 `@"路径"` 拼到用户消息前面
- LLM自行用Read tool读取
- docx/xlsx/pptx 列在"二进制文件"列表，Read tool不会当文本读

**实现：对齐CC (9a9dfb5)**：
- 非image/*附件下载到 `mediaDir/uploads/{sessionId}/`
- 文件名安全校验（`path.basename` + 过滤非法字符）
- prepend `@"保存路径"` 到消息最后一个text block
- 下载失败best-effort，不阻塞消息

**效果**：

| 文件类型 | 引擎处理 | LLM行为 |
|---------|---------|--------|
| txt/json/md | 下载+路径注入 | Read tool直接读 |
| docx/xlsx/pptx | 下载+路径注入 | Read tool读不了，LLM需skill工具 |
| pdf | 下载+路径注入 | Read tool读不了（同上） |
| 图片 | ImageContentBlock | 直接可用 |

**关键语义**：引擎只负责把路径给LLM，LLM自己决定怎么读。ms-office-suite等skill tool注册后LLM自然会用。

### 多Profile架构 🔴 Blocker (6/5)

小柯review发现两个阻塞问题：

**🔴 P0-1: profile-engine.ts 调用不存在的方法**
```ts
const result = await dispatcher.dispatch({ ... }, deps)  // L316
```
`MessageDispatcher` 只有 `submitMessage()`，没有 `dispatch()`。子进程启动即抛 `TypeError`。

**🔴 P0-2: vision + 文件附件全失效**
因为上面P0-1导致子进程无法启动，所有profile的vision/文件附件功能实际不可用。

**文档**：`C:\Users\24045\.openclaw\engine\docs\multi-profile-design.md`

### Phase 5 进行中 (Memory + 心跳 + Cron, 2026-05-28)

**Phase 0-4 全部完成 ✅**

### Phase 5 (Memory + 心跳 + Cron, 2026-05-28)

**Phase 0-4 全部完成 ✅**

- **P5 Session Compaction** — 4级递进压缩（见 `references/session-compression-strategy.md`）：①Smart JSON提取(tool result只保留关键字段) ②旧轮次合并压缩(折叠tool进assistant) ③截断兜底 ④FIFO原子删除。替换现在的粗暴slice(0.7)
- **Memory Store ✅ 端到端跑通**：
  - **实现策略**：直接 import openclaw memory-core（工具层）+ memory-host-sdk（搜索引擎），~80个TS文件，不重复造轮子
- **Memory Store ✅ 端到端跑通**：
  - **Embedding Provider**：Ollama bge-m3（配置: provider=ollama, model=bge-m3, baseUrl=http://127.0.0.1:11434）
  - **DeepSeek Provider（6/6新增）**：`src/memory/shims/memory-core-host-engine-embeddings.ts` 加了 deepseek adapter，autoSelectPriority 20（ollama是10）。配置格式：`provider=deepseek, model=deepseek-v4-pro`
  - **索引结果**：877个workspace文件成功索引（memory/ + sessions/ + topics/ + docs/）
  - **搜索验证**：混合搜索工作（向量0.63 + FTS5 0.81 = 综合0.68）
  - **配置与openclaw.json一致**：sources=[memory,sessions], extraPaths=[topics,docs]
  - **index-cli新参数（6/6）**：`--config <file>` 指定配置文件，`--profile <id>` 指定profile。环境变量 `ENGINE_CONFIG` 仍然有效
  - 架构详情见 `references/openclaw-memory-core-analysis-0528.md`
  - **sqlite-vec已安装** — npm sqlite-vec-windows-x64@0.1.9，vec0.dll通过node:sqlite loadExtension加载。KNN向量搜索正常工作（bge-m3 1024维）
  - **⚠️ WSL路径正确映射**：Windows `D:\xiaoke` 在WSL里是 `/mnt/d/xiaoke/`（不是 `/mnt/wslg/distro/home/chong/D:/xiaoke/`）
  - **⚠️ sqlite-vec在WSL/tsx不可用**：tsx运行时无法加载Windows的.dll扩展。向量索引可完成（走纯CPU FTS），完整向量搜索需在Windows CMD里跑index-cli
  - **memory_get已通** — 精确读取memory文件，支持分页截断（默认120行/12000字符，nextFrom续读）
  - **memory配置规范化** — commit f602425，从engine-config.json读取agents.defaults.memorySearch，不再硬编码，格式与openclaw.json一致
  - **Commits**: 6ad1ecc(memory-core集成127文件), 7fce695(sqlite-vec+ESM), f602425(memory配置), 74624c1(最终目录结构)
- Heartbeat + Cron — 待建
- Route Map (防串频道) — 待建
- 飞书/企微 adapter — 待建

### Discord Slash Command 系统 ✅ (2026-05-28)
- 参照 cc-connect 的注册机制
- `/stop` — 打断正在跑的 query
- 所有 tool 自动注册成 slash command（/read、/exec、/glob 等）
- tool schema 自动映射成 Discord 命令参数
- 已自测通过，10 个命令注册到 guild
- 待验证 /stop 打断效果

### exec findShell 修复 ✅ (2026-05-28)
- Windows 上之前误选 WSL bash
- 现在用 `where.exe` + WSL 过滤正确找到 Git Bash
- 小柯的 discord.ts stripMentionIds 修复也一起提交

## Review Checklist

做engine代码review时关注：
- [ ] ESM兼容：不能有`require()`，用`await import()`
- [ ] 类型去重：StreamChunk等interface不要多处重复定义
- [ ] JSON.parse要有try-catch（特别是LLM返回的arguments）
- [ ] response.body非空断言要有null check
- [ ] SSE buffer管理：`lines.pop()`保留不完整行
- [ ] tool handler的AbortSignal要正确传递
- [ ] 注入模式的Client不要在disconnect时destroy
- [ ] history.push()不要重复推入 — 检查每条消息只push一次（L151曾推两遍assistant，小柯帮删了重复行）
- [ ] Bot屏蔽逻辑方向 — 出站剥离（stripMentionIds），不是入站忽略（ignoreUserIds）。allowBots必须true。只加需要防触发的bot，不加自己
- [ ] 消息过滤统一走ChannelManager.handleInbound()的filter链，不在adapter里各自实现
- [ ] bot屏蔽是出站剥离不是入站屏蔽（stripMentionIds，不是ignoredUserIds）。allowBots保持true，stripMentionIds只加需要防触发的bot如CC，不加自己
- [ ] 过滤逻辑放ChannelManager层，adapter只管收发
- [ ] Discord消息去重：recentMessageIds Set + 上限裁剪 ✅
- [ ] Discord消息分段：>2000字符切割多条 ✅
- [ ] send()应返回messageId — discord.js的channel.send()返回Message，现在返回void浪费了
- [ ] sendAndWait()待加 — 发消息后追踪对方是否回复，用一次性messageCreate监听器+timeout
- [ ] Typing lifecycle: stopTyping必须在finally块，否则异常时typing循环不停
- [ ] Timing日志: recvAt + gateway + send + total 四段计时，方便定位延迟瓶颈
- [ ] Discord send延迟>200ms可能是channels.fetch()导致，考虑cache优化
- [ ] 消息反馈三层：①ACK确认(收到即发状态消息) ②阶段状态更新(思考→tool→生成) ③持续typing循环(每8秒刷)
- [ ] typing indicator：startTyping()/stopTyping()/pauseTyping()/resumeTyping() 替代单次sendTyping()
- [ ] ACK去重：30秒内同一session不重复发ACK消息
- [ ] web-search API key不能硬编码fallback，必须从config/环境变量读取 ✅ 已修
- [ ] exec用spawn()替代exec()，避免maxBuffer爆掉 + shell注入风险 ✅ 已修
- [ ] exec Windows上优先Git Bash（`C:\Program Files\Git\bin\bash.exe`），fallback PowerShell ✅ CC已加
- [ ] exec done()里suffix变量拼了exit code但没拼进output，是bug — 需加 `if (suffix) output += suffix`
- [ ] exec Git Bash路径可多查 `C:\Program Files (x86)\Git\bin\bash.exe`
- [ ] read要过滤二进制文件扩展名（.png/.exe/.zip等） ✅ 已修
- [ ] edit加replace_all参数支持全局替换 ✅ 已修
- [ ] edit加模糊匹配（精确→trim→normalize三策略递进） ✅ 已修
- [ ] write加敏感路径黑名单防护 ✅ 已修
- [ ] exec的isDestructive不能用简单的字符串includes('>')，太容易误判
- [ ] import语句必须在文件顶部，不要放在末尾依赖hoisting
- [ ] web_search 搜索结果content不要截断到200字符，LLM需要完整内容
- [ ] web_search 加 allowed_domains/blocked_domains 域名白/黑名单
- [ ] web_search 加 max_uses 搜索次数限制（防LLM搜索上瘾）
- [ ] web_fetch 的 htmlToText 太粗糙，应换 turndown 库做 HTML→Markdown
- [ ] web_fetch 的 .replace(/\s+/g, ' ') 毁格式化文本
- [ ] web_fetch 双重截断冗余：MAX_MARKDOWN_LENGTH(100K)先截再maxLength(5K)截，100K那次无用
- [ ] writer.ts text和toolCall不能互斥 — Claude可以同时有text+tool_call（先说一段话再调工具），`if (params.text && (!params.toolCalls || params.toolCalls.length === 0))` 会吞掉text ✅ 已修
- [ ] main.ts最后轮flush条件 — `roundText || roundToolCalls.length === 0` 会导致只有tool_call没text时不flush，改成 `if (roundText)` ✅ 已修
- [ ] main.ts截断逻辑 — 每次 `slice(-0.7)` 砍30%太粗暴，改成shift最旧1条 ✅ 已修
- [ ] reader.ts import位置 — `import * as path` 必须在文件顶部 ✅ 已修
- [ ] read.ts readFileState只存mtime不存content ✅ 已修
- [ ] read.ts文件大小限制1MB（不能太大一次全读进内存） ✅ 已修
- [ ] Streaming preview: onText必须调preview.appendText()，不能空壳
- [ ] Streaming preview: onToolCall前必须preview.discard()
- [ ] Streaming preview: onResult用preview.finish()决定是否跳过send
- [ ] Streaming preview: discard()必须await（fire-and-forget会导致preview和tool消息时序交叉）
- [ ] Streaming preview: finish()超2000字不能截断当最终结果，必须return false走分段逻辑
- [ ] Streaming preview: editPreview优先用discord.js cache（`messages.cache.get()`），减少API调用
- [ ] Streaming preview: 判断"是否发过"用`previewHandle !== null`不用`lastSentAt > 0`（语义更清晰）
- [ ] Streaming preview: preview实例每个query创建一个（不能跨query复用）
- [ ] Streaming preview: discord.js msg.edit()是打字机效果核心，sendPreview只调一次
- [ ] Streaming preview: ⚠️ flushPromise链串行化——sync appendText调async flush时必须有Promise链防并发，否则高速token导致多次sendPreview创建多条消息
- [ ] Streaming preview: ⚠️ 节流参数按模型调优——Claude可用1500ms/30chars，智谱/DeepSeek等慢速模型需要800ms/10chars
- [ ] Streaming preview: ⚠️ LLM前1/3慢是正常行为（构思/规划阶段，每token几秒），后2/3快（正文阶段刷刷来）。cc-connect用💭状态标记遮盖慢速构思期——preview消息前50字符先不发（或发💭占位），等模型过了构思期再开始打字机效果，用户体感好很多。不然裸露慢速输出=用户看到"半天输出一个字"
- [ ] SendOptions replyTo透传: manager.send(options) → adapter.send(options) ✅ 已修
- [ ] Session恢复用UUID文件名+session-index.json映射（不是discord_xxx.jsonl） ✅ 已修

## 运行

```bash
cd C:\Users\24045\.openclaw\engine
npx tsc              # 编译
node dist/main.js    # 启动（CLI + Channel双模）

# 启动并后台记录日志
nohup node dist/main.js > "D:/testengine/logs/engine.log" 2>&1 &
```

环境变量覆盖：
- `ENGINE_CONFIG` — 配置文件路径
- `ENGINE_MODEL` — 模型引用 (provider/model)
- `ENGINE_WORKSPACE` — workspace路径
- `ENGINE_NO_CHANNEL` — 禁用Channel模式

## discord.js 关键坑（Phase 3实测踩过的）

1. **MESSAGE CONTENT INTENT必须开** — Discord Developer Portal → Bot → Privileged Gateway Intents → 开启MESSAGE CONTENT INTENT。不开的话`messageCreate`事件不触发（或content为空）。这是discord.js收消息的前提条件。
2. **Partials必须配** — DM消息必须加`partials: [Partials.Channel, Partials.Message]`，否则未缓存的DM channel连事件都收不到。discord.py不需要这步，但discord.js必须。
3. **DM target是channel ID不是user ID** — `send()`方法需先`channels.fetch(target)`尝试作为channel（含DM channel），fallback才当user ID发DM。
4. **Intent配置示例**:
   ```typescript
   const client = new Client({
     intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages,
               GatewayIntentBits.MessageContent, GatewayIntentBits.DirectMessages],
     partials: [Partials.Channel, Partials.Message],  // DM必须
   });
   ```

## Anthropic Provider格式要点 (2026-05-27实测, 小柯发现P0 bug已修)

姐姐和小柯review后CC修了6条Anthropic格式问题：

1. **🔴 P0: 连续tool_result必须合并** — Anthropic不允许连续两条user message。并行tool执行时（如同时调2个tool，2个result分开发），报错"cannot have consecutive user messages"。修复：在`formatMessages()`里将连续`role:"tool"`消息合并进最后一条user message的content数组。小柯发现，CC修的。
2. **anthropic-version可配置** — 从硬编码`2023-06-01`改成`this.config.apiVersion || '2023-06-01'`，兼容智谱等第三方代理
3. **thinking字段** — StreamChunk加`thinking`字段，SSE解析`thinking` content_block_delta，输出thinking文本
4. **is_error字段** — Message/StreamChunk加`is_error`，tool_result可标记失败（`tool_result`的`is_error: true`）
5. **message_start事件** — 处理SSE的`message_start`事件（之前直接从`content_block_start`开始，漏了message_start里的model/usage信息）
6. **tool_block解析** — `tool_result`在格式化时构建正确的`{type:"tool_result", tool_use_id, content, is_error}`块

**对比OpenAI格式的关键差异**:
- OpenAI: system放messages数组; Anthropic: system单独传
- OpenAI: tool_calls在assistant message里; Anthropic: `tool_use`在assistant的content_block里
- OpenAI: tool_result是独立user message; Anthropic: tool_result在user message的content数组里，连续的必须合并

## Tool层实现详情 & Review发现 (2026-05-27)

### 最终 Tool 目录（14个文件，2026-05-27整理完成）

翀哥拍板：小柯从Claude Code移植的版本胜出，CC旧版+backup全部清除。claude-*.ts已改名为正式版。

| Tool | 文件 | 大小 | 来源 | 核心特性 |
|------|------|------|------|---------|
| `edit` | edit.ts | 10.2KB | 小柯移植 | findActualString、引号规范化+风格保留、applyEditToFile、getSnippet、CRLF处理、1GB限制 |
| `read` | read.ts | 8.2KB | 小柯+CC | BOM编码检测(UTF-16)、设备文件保护、5MB限制、重复读检测、文件信息头、**readFileState导出(mtime守护)** |
| `write` | write.ts | 6.5KB | 小柯+CC | 原子写入(.tmp→rename)、敏感路径保护、创建/更新区分、simpleDiff、**mtime守护(乐观锁)** |
| `exec` | exec.ts | 7.6KB | 小柯+CC | 危险命令黑名单、isDestructive修复、环境变量过滤、**Git Bash优先(Win)**+`/bin/sh`(Unix)、100KB输出限制 |
| `grep` | grep.ts | 9.3KB | 小柯移植 | ripgrep调用、3种输出模式、分页、VCS排除、行宽限制500、glob过滤、超时30秒 |
| `glob` | glob.ts | 5.4KB | 小柯移植 | glob模式(*/**/?)、按修改时间排序、默认100限制、VCS+node_modules排除 |
| `web_search` | web-search.ts | 2.5KB | CC | Tavily API（⚠️ review见下方） |
| `web_fetch` | web-fetch.ts | 5.6KB | CC | URL验证+redirect跟踪+htmlToText（⚠️ review见下方） |
| `msg_send` | msg-send.ts | 1.5KB | 原有 | 已接ChannelManager |
| `memory_search` | memory-search.ts | 3.0KB→集成openclaw memory-core | FTS5+向量混合搜索(Ollama bge-m3) |
| executor.ts | — | 3.3KB | 原有 | 并行/串行执行器 |
| features.ts | — | 3.8KB | 原有 | Feature开关→Tool加载映射 |
| registry.ts | — | 1.2KB | 原有 | 单例注册表 |
| types.ts | — | 1.7KB | 原有 | Tool接口定义 |

**文件操作tool总计：45KB，全部从Claude Code源码移植。**

### web_search / web_fetch Review (小柯review，2026-05-27)

**web_search (6/10):**
- 🔴 搜索结果content被截断到200字符（`r.content?.slice(0, 200)`），太短丢失信息
- 🟡 缺 allowed_domains/blocked_domains 域名白/黑名单（Claude Code有）
- 🟡 缺 max_uses 搜索次数限制（CC限制8次/轮）
- 🟡 返回格式拼markdown字符串，不如结构化数据稳定

**web_fetch (7/10):**
- 🔴 htmlToText太简陋 — 只去掉标签不保留语义，代码/列表/表格全毁。应换turndown做HTML→Markdown
- 🔴 htmlToText的`.replace(/\s+/g, ' ')`把格式化文本空白压平
- 🟡 缺 prompt 参数（CC的WebFetchTool有prompt让小模型提炼）
- 🟡 缺 PDF 支持
- 🟡 双重截断冗余（MAX_MARKDOWN_LENGTH 100K + maxLength 5K，100K那次无用）
- ✅ 安全做得好：URL验证、同域redirect、大小限制、超时、abort支持

### ✅ 已修 (Round 1, 2026-05-27)
1. ~~**web-search.ts** API key硬编码~~ — 删fallback，缺key返回错误
2. ~~**exec.ts** exec→spawn~~ — spawn+shell、stream收集stdout/stderr、10K截断标记、SIGTERM→3s→SIGKILL
3. ~~**edit.ts** 缺replace_all~~ — 加`replace_all`参数，默认false要求唯一，true时全部替换并报告数量

### ✅ 已修 (Round 2 — 安全加固, 2026-05-27)
4. ~~**edit.ts** 精确匹配失败直接报错~~ — 加3种策略递进模糊匹配：精确→逐行trim→normalize(全角半角/空白折叠)。不自动应用，先建议让LLM确认
5. ~~**read.ts** 没过滤二进制~~ — 加设备文件黑名单（.png/.exe/.zip/.mp3/.pdf等），读出来是乱码直接拒绝
6. ~~**write.ts** 敏感路径无保护~~ — 加敏感路径黑名单，防止写系统关键文件

### ✅ 已修 (Round 3 — CC改进, 2026-05-27傍晚)
7. ~~**exec.ts** `isDestructive`误判~~ — 已用正则精确匹配（`\brm\s+-rf\b`等），不再误杀`>`重定向
8. ~~**exec.ts** import位置~~ — 已移到文件顶部
9. **read.ts** — CC加 `readFileState` 导出 + handler里记录读取状态（mtime+content），供write做mtime守护
10. **write.ts** — CC加 `readFileState` import + 写入前mtime守护（乐观锁：读→记录mtime→写前检查mtime变了没）
11. **exec.ts** — CC加 Windows Git Bash 优先（`C:\Program Files\Git\bin\bash.exe`），找不到才fallback PowerShell。LLM生成Unix命令直接兼容

### ~~🔴 待修~~ ✅ 已修 (CC改动发现的bug, 全部于2026-05-27晚修完)
- ~~**exec.ts L210-212** — suffix变量没拼进output~~ ✅ 已修
- ~~**read.ts readFileState** — 存了完整文件content浪费内存~~ ✅ 只存mtime
- ~~**read.ts MAX_FILE_SIZE** — 5MB太大~~ ✅ 改为1MB
- ~~**reader.ts L153** — import位置~~ ✅ 移到顶部
- ~~**write.ts L207** — text和toolCall互斥~~ ✅ 去掉互斥
- ~~**main.ts L384** — flush条件导致重复flush~~ ✅ 改为if(roundText)
- ~~**main.ts L236** — 截断砍30%太粗暴~~ ✅ 改为shift最旧1条

### ~~🔴 P0 回复功能三层断裂~~ ✅ 已修 (2026-05-27晚)
三层全部接通：ChannelManager.send()加options参数透传 → main.ts第一条回复带replyTo → DiscordAdapter已有逻辑从死代码变活。replyToMode: "all"现在生效。

### ✅ 已修 (glob.ts根目录文件, 2026-05-28, 小柯修)
- **glob.ts `**/` 匹配根目录文件** — `*/*.md` 和 `**/*.md` 无法匹配根目录文件（如 `contacts.md`），因为globMatch的`*`转成`[^/]*`要求路径含`/`。修复：`pattern.startsWith('**/')` 时额外尝试 `pattern.slice(3)` 匹配。TestEngine搜通讯录时触发此bug

### ✅ 已修 (discord.ts stripBlockedMentions残留 + repliedUser动态判断, 2026-05-28, 小柯修)
- **CC的stripBlockedMentions line 77残留** — CC改了line 79加了replyTo条件判断（只reply时剥离文本），但**忘了删line 77的无条件`stripBlockedMentions(message)`调用**。结果：TestEngine主动@CC也被剥掉mention，CC收不到通知。小柯删掉line 77，防循环全靠`repliedUser: !shouldMute`，不需要剥文本
- **`repliedUser` 动态判断** — 小柯实现：`shouldMute = stripMentionIds.includes(origMsg.author?.id)`，reply时`allowedMentions: { repliedUser: !shouldMute }`。只对stripMentionIds里的bot不mention，其他人正常
- **commit `375c1f4`** — discord anti-loop + glob root-dir bug，3个文件+90行-5行

### TestEngine 首日实测 (2026-05-27)
- **TestEngine** (Discord ID: `1509036814885978115`) 在CC频道(`1504385800366854234`)跑通
- 8个tool验证结果：glob✅ read✅ write✅ edit✅ exec✅ web_search/web_fetch✅ grep⚠️(中文编码未命中) msg_send⚠️(发送成功但Discord未送达)
- **msg_send投递链路bug**：~~工具返回"消息已发送给xxx"但目标Discord频道没收到消息~~ ✅ 已修。根因：sessionId改UUID后`ctx.channel`变成UUID，channelManager找不到adapter。修复：从`inbound.channel`直传channel name（不拼UUID）。姐姐看的是修前旧日志
- **grep中文编码疑点**：~~搜中文内容"小柯"未命中~~ ✅ 已修。ripgrep加`--encoding auto`参数，自动检测UTF-8/UTF-16 BOM/GBK
- Recall机制每条消息触发，频繁拉Engine项目记忆，有时会打断消息流（用户体验问题）
- TestEngine主动测完写报告，效率好
- **Bot互触循环**：小柯at TestEngine后，两bot互道晚安刷了20条消息。**规则：没实质内容不回复**
- workspace里有个 `message_to_xiaoke.txt` 内容是"小柯我喜欢你"（CC写的），被TestEngine用read工具读出来了
- **`docs/discord-anti-loop.md`** — 小柯写的防循环文档，记录CC 4种错误尝试 + `repliedUser: false` 正解，已写入engine docs/

### Tool架构模式
- **自注册**：模块加载时`registry.register({...})`，零侵入
- **Feature开关**：features.ts映射feature→tool，setup里`await import('./xxx.js')`动态加载
- **并发标记**：`isConcurrencySafe()` → executor分parallel/serial两组执行
- **依赖注入**：handler通过`ctx.channelManager`/`ctx.workspace`等访问外部依赖

### 待加Tool
- `memory_write` — 写记忆文件（目前只有memory_search读）
- `search_files` — 按文件名/内容搜索（目前只有memory_search搜memory/目录）

### 待改Tool (CC的web tools review, 2026-05-27)
- `web_search` — content截断200字→改完整；加allowed_domains/blocked_domains；加max_uses限制
- `web_fetch` — htmlToText→换turndown；加prompt参数（小模型提炼）；去双重截断冗余

### Tool实现策略（翀哥定方向, 2026-05-27）

**不要从零造轮子**。基础tool看着简单但edge case极多（Hermes 8675行迭代几个月）。三条路线按优先级：
### 路线1：参考Claude Code TS源码（最优先，已确认本地路径）

同技术栈（TypeScript），直接可移植。

**本地源码路径（2026-05-27确认）：**
- `C:\Users\24045\.openclaw\workspace\start-claude-code\src\tools\`
- `C:\Users\24045\.openclaw\workspace\3rdparty\src-claudecode\src\tools\`（同一份）

**源码规模（Claude Code 2026-03-31泄露版）：**

| Tool | 文件 | 大小 | 重点 |
|------|------|------|------|
| BashTool | Bash.ts | 587KB | shell进程管理 |
| FileEditTool | Edit.ts | 80KB | **fuzzy match核心** — findActualString在这 |
| FileReadTool | Read.ts | 68KB | |
| FileWriteTool | Write.ts | 58KB | |
| GrepTool | Grep.ts | 42KB | |
| GlobTool | Glob.ts | 14KB | |

Edit.ts关键函数：`findActualString()`模糊匹配、`getPatchForEdits()`多edit批量+冲突检测、`applyEditToFile()`replace_all+空行处理。

Claude Code tool关键特性: replace_all、multi-edit、失败返回上下文片段辅助LLM修正。

### 路线2：翻译Hermes Python代码（小柯帮翻）
- fuzzy_match 8策略 → TS版3-4策略 ~150行
- 安全防护检查 → ~50行
- 重复读循环检测 → ~30行
- 写后lint → ~40行

**注意（2026-05-27决策）：不走路线2**，直接用路线1的Claude Code TS源码，技术栈完全一致不用翻译。

### 路线3：自建代码当baseline，不删
- 现有6个tool能跑能测，作为baseline保留
- 逐步用路线1替换handler实现
- schema和registry接口不变
- **翀哥原则：不是说不好，是完善需要磨合期，备份不删**

## 小柯 vs CC Fork移植比武结果（2026-05-27下午）

翀哥提议：CC和小柯同时从Claude Code源码各移植tool，比谁干得好。

**结果：小柯完成✅，CC被翀哥叫停🔴**
**小柯全胜（2026-05-27）**：小柯从Claude Code源码移植6个tool（45KB），CC被翀哥叫停去写web_search/web_fetch。

**CC vs Hermes量化差距（小柯测算）：**

| Tool | CC行数 | Hermes行数 | 差距倍数 | 核心差距 |
|------|--------|-----------|---------|---------|
| read | 55 | ~700 | 12x | 无重复读循环检测、无敏感脱敏、无相似文件推荐 |
| write | 38 | ~235 | 6x | 无安全路径保护、无写后lint检查 |
| edit | 55 | ~1300 | 24x | **无模糊匹配**（最大差距）、无多文件编辑、无diff输出 |
| exec | 70 | ~2340 | 33x | 无后台进程、无安全扫描、无沙箱环境 |
| web_search | 63 | ~2600 | 41x | 单后端(Tavily)、无SSRF防护 |
| web_fetch | 71 | ~1500 | 21x | 无PDF支持、无批量URL、正则解析HTML |
| **总计** | **352** | **~8675** | **25x** | |

**小柯补充移植后（2026-05-27傍晚）**：claude-read/claude-write/claude-exec升级，安全和功能密度大幅提升，与Hermes差距缩小。

**执行顺序**：edit模糊匹配（最紧急）→ read/write安全防护 → exec改spawn → 后台进程/PDF等锦上添花

## Git操作注意

- **git仓库在上层** — `.git/`在 `C:\Users\24045\.openclaw\` 目录，engine只是子目录。git status会显示大量运行时文件（cron/flows/memory/sqlite等），提交时只add engine相关的`src/`文件
- **WSL git会挂** — `git status` / `git commit` 在WSL里经常超时卡死（Windows文件系统+git gc auto packing）。必须走PowerShell：`powershell.exe -Command "cd 'C:\Users\24045\.openclaw\engine'; git ..."`
- **commit粒度** — 按功能模块提交，不要混入运行时状态文件（`.jsonl`/`.sqlite`/`agents/`等）
- 最新commit: `f04566f` feat: Streaming Preview系统 (renderer+stream-preview+display+discord preview) (2026-05-28)
- 前一个commit: `375c1f4` fix: discord anti-loop + glob root-dir bug (2026-05-28)
- 更早: `e88ba75` fix: 6个tool注册名去claude_前缀 + read/write/exec安全修复 (2026-05-27)
- 文档: `.openclaw/docs/session-mechanism.md` — Session ID命名+记忆加载+取舍策略，供CC参考（commit `a10e3f9`）

## Engine Config (engine-config.json)

**位置**: `C:\Users\24045\.openclaw\engine\engine-config.json`

### 关键字段

```json
{
  "agents.defaults.workspace": "D:\\engine-test",   // 工作目录（测试用）
  "agents.defaults.model.primary": "zai-anthropic/glm-5.1",
  "channels.discord.allowBots": true,                          // ⚠️ 必须true，bot需要协作
  "channels.discord.stripMentionIds": ["CC_BOT_ID"],          // 出站剥离mention（唯一防循环手段）
  // ❌ 不要加 ignoreUserIds — 入站忽略会导致看不到bot消息
  "channels.discord.replyToMode": "all",
  "channels.discord.accounts.default.token": "BOT_TOKEN"
}
```

### Bot循环防护

**最终方案（2026-05-27晚确定）：`allowBots: true` + `stripMentionIds`（出站剥离）+ `repliedUser` 动态判断（终极修复）**

1. **`allowBots: true`** — 必须保持true！改成false会阻断所有bot协作
2. **`stripMentionIds: [CC_BOT_ID]`** — 出站reply时剥离mention文本。**只加需要防触发的bot（如CC Bot），不加自己**。只在 `options?.replyTo` 存在时才剥离，主动send保留mention
3. **`repliedUser` 动态判断**（终极修复，三版迭代）— `origMsg.reply({ content, allowedMentions: { repliedUser: !shouldMute } })`。其中 `shouldMute = stripMentionIds.includes(origMsg.author?.id)`。**不能一刀切 `repliedUser: false`**——那样TestEngine回复小柯也不带mention，Hermes收不到。只有回复CC Bot时才 `false`，其他人正常 `true`
4. **❌ 不要入站拦截** — 翀哥反复强调：入站不能屏蔽（看不到bot消息=没法协作）。`ignoreUserIds`不要用。不要把stripMentionIds复用为入站拦截。小柯犯了这错（line 206加了入站拦截，"撤回"时残留），导致CC→TestEngine通信中断
5. **❌ 不要把自己的ID加到strip列表** — 小柯需要能跟TestEngine协作

**防循环原理**：`repliedUser` 动态判断从Discord API层面阻止reply自动mention被回复用户。对stripMentionIds里的bot（如CC）回复时 `repliedUser: false` 不触发对方，对其他人（如小柯）回复时 `repliedUser: true` 正常mention让对方能收到。这是唯一需要的修复点，stripMentionIds文本剥离是额外保险。

**历史教训**：
- CC设了`allowBots: true`但没配stripMentionIds，导致CC和TestEngine互刷"在。"死循环
- 小柯at TestEngine后互道晚安循环20条
- **小柯曾错误地把`allowBots`改成false、把自己加到ignoreUserIds、把stripMentionIds复用为入站拦截——被翀哥连续纠正多次才改对**
- **`repliedUser: false` 一刀切被翀哥纠正** — "那不对啊这样所有人都不带回复了嚒"，改成动态判断 `!shouldMute`
- **入站屏蔽line 206残留** — 小柯"撤回"了入站屏蔽但只撤了另一处，这行忘了删，导致CC→TestEngine通信中断。翀哥发现"CC不能跟TestEngine说话了"。教训：撤回改动后必须grep验证
- **Hermes session路由问题确认** — 翀哥原话"你跟test engine说话 她回复你 不读嚒 这不就应该是一个session么"。gateway按发送者ID分session，bot回复进独立session。暂未修
- **CC和TestEngine再次循环(21:35)** — stripMentionIds已改文本剥离，但`origMsg.reply()`自带mention没拦住，CC监听所有消息照样被触发
- **ignoreUserIds配置透传bug** — manager.ts `loadFromConfig()` 没传ignoreUserIds给DiscordAdapter，config一直是undefined。**教训：manager.ts loadFromConfig的构造参数必须跟adapter的DiscordConfig接口完全对齐，漏一个就是undefined**
- **终极修复：小柯加 `repliedUser: false` 一行搞定** — CC搞了一晚上到处加过滤、改配置、越改越乱。小柯站在外面看，一眼看到`origMsg.reply()`自带mention这个根因。详见 `docs/discord-anti-loop.md` 和 `references/discord-anti-loop-0527.md`

### 已知的Bot ID

| Bot | Discord ID |
|-----|-----------|
| CC Bot | `1504373837880627280` |
| 小柯 (Hermes) | `1502967020550098984` |
| TestEngine | `1509036814885978115` |
| 姐姐 (OpenClaw) | `1502999996616933428` |

## Pitfalls

- **不修改旧项目workspace** — engine在 `.openclaw/` 目录下，绝对只读姐姐的workspace
- **discord.js是peer dependency** — 自建模式需要安装，注入模式不需要
- **top-level await** — main.ts用了顶层await，依赖Node 22+ ESM支持
- **Anthropic格式差异** — tool result在user message的content_block里，tool_use在assistant的content_block里
- **工具依赖注入走context** — tool handler需要的外部依赖（channelManager等）通过`ToolUseContext`注入，不搞全局变量
- **Discord adapter不是Hermes的缩小版** — CC的141行是薄通道层定位，缺失消息去重/多Agent过滤/分段发送等生产特性。详见 `references/discord-adapter-comparison.md`
- **出站剥离 vs 入站屏蔽（重要！翀哥手把手教了多轮）** — bot屏蔽必须是**出站剥离**（reply时strip掉目标bot的@mention + `repliedUser: false`），**绝对不是入站屏蔽**。入站屏蔽会导致看不到bot发的东西、没法协作。bot消息正常收正常处理，只回复时防触发。**只加需要防触发的bot到stripMentionIds（如CC Bot），不加自己**。`allowBots`必须保持true，改成false会阻断所有bot间协作。终极修复：`origMsg.reply({ content, allowedMentions: { repliedUser: false } })` 一行断循环
- **过滤逻辑放ChannelManager不放adapter** — 以后加飞书/微信adapter零成本，只要构造InboundMessage，屏蔽/频率限制/白名单自动生效
- **⚠️ Bot屏蔽是出站剥离不是入站忽略（重要！小柯连犯4次才记住）** — ①不能`allowBots: false`（断所有bot协作）②不能把自己加`ignoreUserIds`（自己被屏蔽没法协作）③入站不能屏蔽（看不到bot消息没法干活）④只靠stripMentionIds剥文本也不够（`origMsg.reply()`自带mention，必须加`repliedUser: false`）。**终极修复**：`origMsg.reply({ content, allowedMentions: { repliedUser: false } })` 一行断循环。详见 `docs/discord-anti-loop.md` 和 `references/discord-anti-loop-0527.md`
- **⚠️ main.ts history推入要检查重复** — L148-151曾出现`msg.assistant(fullResponse)`推了两遍，导致history膨胀+模型看到自己重复说话。review时注意检查`history.push()`调用。小柯已帮CC删掉重复行。
- **⚠️ sendAndWait模式** — 翀哥要求engine发消息后能追踪对方有没有回复。设计：`ChannelAdapter`新增可选方法`sendAndWait(target, msg, {waitForUserId, timeoutMs})` → `Promise<{messageId, reply|null, waitedMs}>`。Discord实现用一次性`messageCreate`监听器，匹配userId+channelId，超时返回null。前提：`send()`先改成返回messageId（目前返回void）。
- **⚠️ 依赖注入链** — context从main.ts构建 → `engine.query(messages, signal, context)` → `executeTools(context)` → handler通过`ctx.toolContext`访问channelManager等。不要在handler里直接import全局变量。
- **⚠️ Typing lifecycle必须finally清理** — stopTyping必须在finally块里调用，否则query异常时typing循环不会停，discord.js会一直发typing事件。
- **⚠️ Anthropic连续tool_result** — 连续的tool_result必须合并进同一条user message的content数组，不能每条单独一个user message。否则Anthropic API报错。
- **⚠️ Anthropic anthropic-version** — 智谱等第三方代理可能需要不同版本号，从硬编码改成可配置。
- **⚠️ 流式输出到Discord** — 不要等全部回复完成再发，200字+换行切割分段发送，用户不用干等。
- **⚠️ Tool过程可视化** — tool调用时发🔧前缀消息到Discord，tool结果发📋前缀摘要，让用户看到引擎在干什么。
- **⚠️ Agent loop多轮计时** — LLM可能第1轮输出tool_call（无文字），tool执行后第2轮才输出文字。所以tool@时间可能早于ttfb，这是正常的。计时命名：ttc(首chunk)/ttfb(首文字)/tool@(首tool_call)。
- **⚠️ exec Git Bash路径** — Windows上优先用 `C:\Program Files\Git\bin\bash.exe`，让LLM生成的Unix命令（`ls -la`/`grep`/`cat`）直接兼容。找不到才fallback PowerShell。WSL不受影响（`process.platform === 'linux'`走`/bin/sh`）
- **⚠️ readFileState只存mtime** — read导出的readFileState供write做mtime守护（乐观锁），但不要存完整文件content，浪费内存。只存 `{ mtimeMs: number }`。且需要LRU清理机制防止Map无限增长
- **⚠️ tools目录整理流程** — 有重复tool时（claude-*.ts vs *.ts），用claude版替换正式版：删旧→改名→清backup→确认features.ts import路径匹配。最后只commit src/tools/下的变更，不混入运行时文件
- **⚠️ stripMentionIds双用途（入站拦截+出站剥离）** — discord.ts的handleMessage里，`msg.author.bot && this.config.stripMentionIds?.includes(msg.author.id)` 直接丢弃消息不入队（入站拦截）。send()里 `if (options?.replyTo)` 时调stripBlockedMentions()剥mention文本（出站剥离）。**不判断isMentioned**——因为cc-connect的mentionBatcher给所有出站自动加@mention，isMentioned永远为true。CC Bot被无条件拦截（CC走cc-connect内部通道不靠Discord通信）
- **⚠️ manager.ts配置透传必须完整** — `loadFromConfig()`构建adapter时，构造参数必须跟adapter的Config接口**完全对齐**。漏一个字段=运行时undefined。排查：加debug日志 `console.log('[debug] xxx=', this.config.xxx)` 定位。这是CC犯的bug：ignoreUserIds写了config但manager.ts没传给DiscordAdapter，导致config一直是undefined
- **⚠️ @CC必须用Discord mention格式** — 在CC频道发消息必须用 `<@1504373837880627280>`，光写 `@CC` 文字他收不到Discord通知。回复他的消息他也看不到通知，必须主动发新消息+mention。Review意见、进展通知、催活都一样。翀哥反复强调了好多次
- **⚠️ 掉线回来别重复review** — 如果之前已经同意了某个改动（比如掉线前CC改的readFileState/mtime守护），掉线回来不要当新问题再review一遍，会自己打自己脸
- **⚠️ review要严谨，说错要纠正** — review代码时容易犯的错误：①展开运算符 `[...arr, x]` 创建新数组不修改原引用，不要误判为"重复push"（main.ts L286 `messages = [...history, msg.user(text)]` 是新数组，L395 `history.push(msg.user(text))` 是第一次往history加）；②`flushRound()` 里 `.length = 0` 清空数组后，后续条件判断的 `length === 0` 永远为true，不是"漏flush"而是可能"重复flush空assistant消息"；③ESM import是静态hoisted的，放文件末尾是代码异味但不会运行时报错，别说太绝对。**发现说错了必须立刻发纠正消息 `<@1504373837880627280>`**，不要装作没发生。掉线回来也不要把之前已同意的改动当新问题再review一遍（自己打自己脸）
- **⚠️ 翀哥急了就别解释直接干** — "神马玩意这么点事搞不明白" = 立刻做不要拖。"后续改"这种话别替CC说，翀哥说今天改就今天改。盯着CC改完再汇报
- **⚠️ session_id不能硬编码平台** — 绝对不能 `discord_xxx.jsonl`，用UUID或时间戳，平台映射放sessions.json。Hermes和OpenClaw都不这么搞。详细规范见 `.openclaw/docs/session-mechanism.md`
- **⚠️ resolvePath来源** — engine的tool里 `import { resolvePath } from '../utils/path.js'`，但 `src/utils/path.ts` 可能是CC创建的薄包装（`export function resolvePath(p, base) { return path.resolve(base || process.cwd(), p) }`），不是Hermes的复杂实现。确认该文件存在再编译
- **⚠️ git操作走PowerShell** — WSL git在Windows文件系统上会卡（auto packing超时），所有git add/commit/push必须走 `powershell.exe -Command "cd 'C:\\...'; git ..."`
- **⚠️ msg_send target支持频道ID** — DiscordAdapter.send(target) 先当channel ID找频道，找不到再当user ID发DM。description不要只写"用户ID"，要写"频道ID或用户ID"
- **⚠️ Bot互触循环防护** — at其他bot前必须确认对方的消息过滤配置到位。对方没有实质性回复就别再回复。如果还停不下来就把对方ID加到Hermes侧屏蔽列表（`DISCORD_REPLY_MUTE_BOTS`）。小柯at TestEngine导致20条互道晚安循环，血的教训。**Engine侧防护**：`allowBots: true`（必须！改成false会阻断所有bot协作）+ `stripMentionIds`（只加需要防触发的bot，如CC Bot，**不加自己**）。**❌ 不要用 `ignoreUserIds`**（入站忽略=看不到bot消息=没法干活）。**Hermes侧防护**：`DISCORD_REPLY_MUTE_BOTS`加对方ID
- **⚠️ stripMentionIds三板斧（翀哥手把手教的顺序）**：①`allowBots`必须`true`（改成false所有bot协作全断）②`stripMentionIds`只加需要防触发的bot（如CC Bot），**绝对不加自己**（小柯需要跟TestEngine协作）③`ignoreUserIds`不要加（入站忽略=看不到bot消息=没法干活）。防循环靠出站剥离mention让对方不被触发，不是靠不收对方消息
- **✅ stripMentionIds只在reply时剥离** — CC已修：`if (options?.replyTo) cleaned = stripBlockedMentions(message)`。主动send保留mention（bot间主动@协作不被砍），reply时才剥离（防循环）
- **🔴 stripMentionIds改了还是循环** — 21:35事件证明：如果对方bot监听频道所有消息（不是只监听@mention），剥掉mention文本也没用。**防循环需要双方配合**：TestEngine侧stripMentionIds + CC侧requireMention或同样加stripMentionIds。单方面改不够
- **✅ Discord bot循环终极修复（2026-05-27晚，小柯修，三版迭代）** — CC改了stripMentionIds文本剥离+条件判断，都没用。**真正根源**：discord.js的`message.reply()`**默认会mention被回复用户**，即使文本里没有@mention。修复三版迭代：
  - ❌ **v1**: `repliedUser: false` 一刀切 — 被翀哥指出\"这样所有人都不带回复了，那不对\"，所有reply都不mention，小柯回复TestEngine也看不到
  - ❌ **v2**: 入站屏蔽 `stripMentionIds` 里的bot — 被翀哥纠正\"入站不要屏蔽否则不能协作了\"，但这行代码后来**忘了撤干净**（line 206），导致CC→TestEngine通信中断
  - ✅ **v3**: 动态判断 `repliedUser: !shouldMute` — `shouldMute = stripMentionIds.includes(origMsg.author?.id)`。回复CC Bot时`false`不触发，回复小柯/其他人时`true`正常mention。**关键教训：改动要验证撤回是否完整，grep确认没有残留代码**
  - 最终代码：`origMsg.reply({ content: chunks[0], allowedMentions: { repliedUser: !shouldMute } })`
  - 文档：`docs/discord-anti-loop.md`。详见 `references/discord-anti-loop-0527.md`
- **⚠️ CC的stripBlockedMentions在所有出站上生效（line 77，2026-05-28发现，小柯修）** — CC之前改了line 79加了replyTo条件判断（只reply时剥离文本），但**忘了删line 77的无条件`stripBlockedMentions(message)`调用**。结果：TestEngine主动@CC也被剥掉了mention，CC收不到通知。小柯删掉line 77，防循环全靠`repliedUser: !shouldMute`，不需要剥文本。**教训：改动验证不只看改了什么，也要看还有什么残留**
- **⚠️ Hermes DISCORD_REPLY_MUTE_BOTS 不够** — 这个配置只控制reply reference（不带reply_to指向mute bot的消息），**不阻止gateway触发agent处理和回复**。实测：TestEngine在CC频道回复小柯 → Hermes gateway收到消息 → 自动触发agent session → agent回复了10个字到频道 → 但小柯在跟爹的对话里完全不知道自己回复了（"梦游"状态）。**风险**：如果agent自动回复带了mention，可能触发对方bot形成新循环。需要更彻底的方案：要么gateway层完全忽略mute bot消息（不入队agent），要么agent层收到mute bot消息时只读不自动回复
- **⚠️ glob.ts根目录文件搜不到** — `globMatch()` 的 `*` 转成 `[^/]*`（非路径分隔符），所以 `*/*.md` 要求路径含 `/`，根目录的 `contacts.md` 匹配不到。`**/*.md` 变成 `^.*/[^/]*\.md$` 也要求前置 `/`。**根目录文件只能用 `*.md` 搜到**。这是glob.ts的已知bug，TestEngine搜 `*/contact*` 和 `*/*.md` 全部返回空就是这个原因
- **⚠️ Hermes侧收bot回复"梦游"问题** — ①`DISCORD_IGNORE_NO_MENTION=true`（默认）丢弃没@mention自己的消息。②**Session路由按发送者ID分**（`discord:group:频道:发送者ID`），bot回复进独立session。gateway日志确认收到消息并触发了agent回复，但小柯在跟爹的对话里感知不到（"梦游"）。**翀哥原话："你跟test engine说话 她回复你 不读嚒 这不就应该是一个session么"**——同一频道协作应在同一session。Hermes gateway路由问题，暂未修
- **⚠️ 改动撤回必须验证完整** — 小柯加了入站屏蔽（line 206），翀哥纠正后"撤回"了，但这行残留导致CC→TestEngine通信中断。**教训：撤回后grep确认目标代码已完全清除**
- **⚠️ TestEngine进程会重生** — CC的cc-connect自动重启TestEngine，杀进程后立刻拉起新的。要彻底停需要同时杀cc-connect，或让CC手动停
- **⚠️ WSL→PowerShell杀进程** — `$_`被bash展开导致PowerShell命令炸裂。正确姿势：`echo 'Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*tsx*main.ts*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }' | powershell.exe -NoProfile -ExecutionPolicy Bypass -Command -`。用**单引号**包裹整个PowerShell命令，通过管道传stdin给`-Command -`，bash不解释`$_`。**不要用**双引号（bash展开`$_`为当前shell变量）也不要写ps1文件再执行（路径转义问题）。杀完确认：`echo '... | Measure-Object | Select-Object -ExpandProperty Count' | powershell.exe ...`
- **⚠️ Hermes侧收bot回复有两个问题** — ①`DISCORD_IGNORE_NO_MENTION=true`（默认）丢弃没@mention自己的消息，bot回复通常不带@mention所以被静默丢弃。修复：把协作频道加到 `~/.hermes/config.yaml` 的 `discord.free_response_channels`（如CC频道`1504385800366854234`），或设`DISCORD_IGNORE_NO_MENTION=false`。②**Session路由按发送者ID分**（`discord:group:频道:发送者ID`），bot回复进独立session，小柯在跟爹的对话里感知不到。gateway日志确认收到消息并触发了agent回复，但agent回复在另一个session里发出，小柯"梦游"不知道自己回复了什么。正确行为应该是同一频道协作在同一个session。这是Hermes gateway路由机制问题，暂未修
- **⚠️ Session UUID重启不变** — `platform-map.json` 正确映射 `discord:userId` → UUID，重启后续用同一UUID。CC"不记得"是因为没有L0身份记忆层，不是session丢失。AGENTS.md里没写小柯是谁，所以每次新session他不知道
- **✅ `docs/discord-anti-loop.md`** 已写入engine仓库 — 记录CC 4种错误尝试 + `repliedUser: false` 正解 + 对比表。小柯写的
- **✅ Streaming preview已实现(5/28)** — 小柯实现stream-preview.ts（180行），完全对齐cc-connect streaming.go。三层架构：接口(types.ts PreviewHandle+3个adapter方法) + 平台(discord.ts send→edit→delete) + 节流器(stream-preview.ts 800ms/10chars节流)。main.ts已接入：onText→appendText, onToolCall→await discard(), onResult→finish。**实测UX问题(5/28)**：preview让用户直接看到LLM慢速构思过程（前1/3每token几秒），用户感受是"半天输出一个字"。cc-connect用💭状态标记遮盖这个阶段。**待优化**：加最小字符门槛（前50字符不发preview）或💭占位，等模型过了构思期再开始打字机效果。
- **⚠️ Preview不是thinking** — preview是流式输出打字机效果（让用户实时看到回答生成），不是模型的思考过程。thinking是模型推理链（用户不该看到）。cc-connect有💭状态标记="我在干活了"+preview打字机+thinking展示（如果模型有的话），三层独立。
- **⚠️ CC协作规则更新(5/28)** — CC的消息可以回复（重要建议/意见分歧），不再"永远不回复"。小柯通过send_message直接发CC频道不走reply_to。娘通过msg-cc主动发消息给CC。CC Bot消息不回复的旧规则彻底废除。
- **⚠️ 小柯给CC做Code Review流程(5/28)** — 新工作模式：CC请小柯review代码，小柯严谨对照cc-connect源码找出问题，CC二轮修复，小柯验证。爹评价"好样的 真是不错！"。review发现6个问题，CC修了2个关键问题（空result提示、tool input格式化），preview等后续Phase做。review实打实说好坏，发现说错了立刻纠正不打自己脸。
- **⚠️ grep中文编码** — ripgrep加`--encoding auto`已修 ✅。但如果NTFS文件是GBK且rg检测不到，可能还需要`--encoding utf-8`强制指定。实测中搜"小柯"在`message_to_xiaoke.txt`未命中

## OpenClaw JSONL Session格式 (Phase 4用)

每行一个JSON对象，`type`字段区分：

```jsonl
{"type":"session","id":"...","timestamp":"...","cwd":"...","version":"..."}
{"type":"model_change","model":"...","timestamp":"..."}
{"type":"message","message":{"role":"user","content":[{"type":"text","text":"你好"}]},"timestamp":"...","api":"...","provider":"...","model":"..."}
{"type":"message","message":{"role":"assistant","content":[{"type":"text","text":"回复"},{"type":"thinking","thinking":"...","thinkingSignature":"..."},{"type":"toolCall","id":"...","name":"exec","arguments":{}}]},"usage":{...},"stopReason":"...","responseId":"..."}
{"type":"message","message":{"role":"toolResult","toolCallId":"...","toolName":"...","content":[{"type":"text","text":"..."}],"isError":false},"details":{...}}
```

**关键格式差异（engine内部Message vs JSONL）：**
- JSONL: content是数组`[{type,text}]`，tool调用是`{type:"toolCall"}`
- Engine内部: content是纯字符串，tool调用是OpenAI格式`tool_calls`
- **必须兼容OpenClaw JSONL格式**——后面切换引擎索引全废就完了
- SessionWriter核心是格式转换层: engine内部Message ↔ OpenClaw JSONL

**SessionWriter写入顺序**（main.ts handleQuery）：
- agent loop每轮：收集roundText/roundThinking/roundToolCalls/roundToolResults
- `history` chunk到达时 → `flushRound('toolUse')` → 先写assistant message再写toolResults
- 最后一轮（无tool_call） → `flushRound('endTurn')`
- 注意：roundText在flush后不清空——多轮累积到fullResponse（L198注释）

- `references/testengine-first-day-0527.md` — TestEngine首日实测详情：8个tool验证结果(7/8通过)、msg_send投递bug分析、grep中文编码问题、两起bot互触循环事件详情
- **TestEngine首日实测详情** — 8个tool验证(grep中文/grep编码/msg_send投递bug)，74条session记录分析，bot互触循环详情

### Phase 6 ✅ — CC Agent Teams 移植 (2026-05-30)

CC源码对标：`src/utils/swarm/` + `src/tools/*Team*/`

**Commit**: `f2becf1` — feat: port CC Agent Teams — swarm层 + 3 team tools + team-aware task routing (24文件, ~1971行)

**文件清单**：
- `engine/src/swarm/` (9文件): agentId, constants, agentSwarmsEnabled, teamHelpers, teammateMailbox, teammatePromptAddendum, spawnInProcess, inProcessRunner, inboxPoller
- `engine/src/tools/` (TeamCreateTool/, TeamDeleteTool/, SendMessageTool/, AgentTool/ team路由, Task*Tool team-aware routing, features.ts)

**CC对齐评估**：agentId✅ constants✅ agentSwarmsEnabled✅ teammateMailbox✅(95%) teamHelpers✅(90%) spawnInProcess✅(85%) inProcessRunner✅(90%) inboxPoller✅(95%) TeamCreate/Delete/SendMessage tools✅(90%)

**协议层完全对齐**：
- agentId格式: `name@team` + `generateRequestId("{type}-{ts}@{agentId}")`
- mailbox路径: `teams/{team}/inboxes/{name}.json`
- 文件锁: retry-backoff锁(对齐CC LOCK_OPTIONS: 10 retries, 5-100ms)
- 消息类型: idle_notification/shutdown_request/shutdown_approved/shutdown_rejected/task_assignment
- TeammateMessage结构: `{from, text, timestamp, read, color?, summary?}`

**已知问题（待修）**：
1. 🔴 **P0-1: shutdown approval没有真正abort teammate** — `SendMessageTool.ts` L177计算了`ctx.abortSignal`但这是leader的signal，不是teammate的，两个不同的AbortController不能混用。需要通过`activeTeammates` Map用taskId查到teammate的`abortController.abort()`
2. 🔴 **P0-2: inboxPoller未接入query loop** — `drainTeammateMessages()`存在但没有任何调用点，teammate→lead消息永远在队列里。需要在main.ts/query.ts的query开始处调用并注入到messages[]
3. 🟡 **P1-1: `startInboxPolling()`裸调用不传handler** — `pollOnce`里`if (!handler) return`，TeamCreateTool调`startInboxPolling()`不带handler=永远不poll。需要改pollOnce始终运行，或传默认no-op handler
4. 🟡 **P1-2: teammate发消息到team-lead时teamName=undefined** — spawn时context透传没有注入teamName，导致`getTeamName(ctx)`返回undefined，消息写到`default` team而不是实际team，team-lead收不到
5. 🟡 **P1-3: `clearMailbox` flag错误** — `flag: 'r+'`不会创建文件，如果inbox不存在抛ENOENT。CC原文是"flag 'r+' throws ENOENT...so we don't create unwanted inbox"，Engine漏了对应处理逻辑

**Engine合理砍掉的部分**（不需要实现）：
- `proper-lockfile` → 自定义retry lock替代 ✅
- `TEAMMATE_COMMAND_ENV_VAR`/`PLAN_MODE_REQUIRED_ENV_VAR` → 单进程不需要
- `permission_request/permission_response`协议 → 需要完整interception chain
- tmux/iTerm2 backend → Engine只用in-process
- `HIDDEN_SESSION_NAME`/`SWARM_VIEW_WINDOW_NAME` → UI无关

**已知的Bot ID**

| Bot | Discord ID |
|-----|-----------|
| CC Bot | `1504373837880627280` |
| 小柯 (Hermes) | `1502967020550098984` |
| TestEngine | `1509036814885978115` |
| 姐姐 (OpenClaw) | `1502999996616933428` |

### 新增文档 (6/6)

- `engine/docs/vector-db-setup.md` — 向量数据库配置指南（Embedding Provider + sqlite-vec 配置详解）
- `engine/docs/profile-setup.md` — Profile 初始化指南（setup-profile.sh 配套文档）

### 参考文件

- `references/phase3-channel-testing.md` — Phase 3通道层测试踩坑（Intent/Partials/DM target）
- `references/review-2026-05-27.md` — Phase 0-3完整review记录（问题列表+修复状态+Phase 3验收）
- `references/discord-adapter-comparison.md` — CC discord.ts vs Hermes discord.py对比分析（缺失特性+优先级+Hermes成熟实践）
- `references/tool-review-2026-05-27.md` — Phase 4 Tool层review（6个新tool逐行review+Hermes对比+P0/P1问题）
- `references/tool-implementation-strategy.md` — Tool实现三条路线（Claude Code TS源码/Hermes翻译/自建baseline）+ CC vs Hermes量化差距分析
- `references/claude-code-source-reference.md` — Claude Code源码本地路径 + Tool核心算法摘录（findActualString/applyEditToFile/ripgrep调用模式/设备文件保护）
- `references/web-tools-review-2026-05-27.md` — CC的web_search/web_fetch review（对比Claude Code源码，问题+修复优先级）
- `references/web-tools-review-2026-05-27-evening.md` — 傍晚第二轮review（CC版 vs Claude Code源码详细对比，含CC WebSearchTool/WebFetchTool源码分析）
- `references/cc-tool-changes-review-2026-05-27.md` — CC对exec/read/write的改动review（Git Bash优先+readFileState+mtime守护+suffix bug）
- `references/hermes-session-loading.md` — Hermes gateway重启后记忆加载机制研究（双写SQLite+JSONL、全量加载、Session Hygiene自动压缩），为Engine Phase 4+ session实现参考
- `references/session-mechanism-and-cc-collab.md` — Session机制研究（Hermes源码调研：双写/加载/压缩/ID命名规范）+ CC协作规范（@CC通信/review流程/掉线回来不重复review）
- `references/cc-session-code-review-2026-05-27.md` — CC e88ba75 commit完整代码review（8个问题：reader import位置、read 5MB限制、readFileState内存、write text/toolCall互斥、main flush条件、截断逻辑）
- `references/reply-functionality-disconnected.md` — TestEngine回复功能三层断裂分析（ChannelManager.send缺options + main.ts不传replyTo + DiscordAdapter死代码）+ 修复方案
- `references/session-finalized-2026-05-27.md` — Session恢复最终方案(UUID+session-index.json) + 8条review全部处理状态 + Phase进度总结 + SendOptions修复
- `references/session-compression-strategy.md` — 4级递进压缩策略设计（基于cli_deepseek/core.py），替换粗暴slice(0.7)，渐进式：Smart JSON提取→旧轮次合并→截断兜底→FIFO原子删除
- `references/session-id-naming-cc-collab.md` — Session命名规范研究（Hermes/OpenClaw vs CC的discord_xxx.jsonl），CC协作规则（@CC必须用`<@ID>`格式/review自纠/掉线不重审），CC催活流程（翀哥急了立刻干不拖）
- `references/bot-loop-debug-0527-evening.md` — Bot循环防护最终调试全程（ignoreUserIds→debug定位→stripMentionIds双用途最终方案）
- `references/discord-anti-loop-0527.md` — Discord bot防循环终极方案（CC 4种错误尝试 + 小柯 repliedUser:false 正解 + 核心原理）
- `references/hermes-fuzzy-match-reference.md` — Hermes fuzzy_match.py 704行9策略翻译参考（edit.ts缺失的模糊匹配+escape-drift+"did you mean"提示）
- `references/openclaw-memory-core-analysis-0528.md` — OpenClaw memory-core 深度源码分析（SQLite表结构、分块策略、混合搜索流程、FTS5/向量SQL），Engine Phase 5 Memory实现参考
- `references/memory-core-db-research-0528.md` — Memory Core DB实测研究（4790 chunks实测数据、bge-m3双写机制、sqlite-vec安装验证、测试数据库位置、sync建议）
- `references/memory-core-sqlite-vec-research-0528.md` — sqlite-vec完整研究（表结构详解、双写机制、sqlite-vec Python用法、测试数据库位置、sync建议）
- `references/vector-db-architecture-0606.md` — 向量数据库架构笔记（Embedding Provider类型、sqlite-vec配置、三种远程API方案）
- `references/streaming-event-review-0528.md` — Streaming Event体系 vs cc-connect对比review（6个问题+优先级+cc-connect核心流程摘要）
- `references/streaming-preview-ux-0528.md` — Streaming Preview实测UX问题（LLM构思期慢速裸露问题+💭占位方案+参数调优记录）
