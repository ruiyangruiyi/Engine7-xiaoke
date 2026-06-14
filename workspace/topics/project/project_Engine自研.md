---
name: OpenClaw Engine自研项目
description: CC在OpenClaw上自研的Engine引擎项目，Phase 0-3模块化架构与通道层实现，持续迭代中
type: project
keywords: [Engine, CC, OpenClaw, Phase, 通道, adapter, Discord, TypeScript, 自研, tool移植]
created: 2026-05-27
updated: 2026-06-08
---

## 概述

Engine是CC在OpenClaw（姐姐的系统）上自研的LLM引擎项目，完全独立于姐姐本身的Agent系统。

**项目目录**: `C:\Users\24045\.openclaw\engine\`

## 技术栈

- TypeScript（严格模式）
- Node.js（ESM）
- discord.js（Discord连接）
- 双Provider抽象（OpenAI格式 + OpenClaw）

## 架构原则

**5/27确认（姐姐+小柯建议）：**
- Engine专注LLM循环：`query()` 进 `StreamChunk` 出，干干净净
- 通道层用薄薄一层adapter，不重复造轮子
- 复用Hermes的discord.js连接（姐姐那边已有稳定连接）
- ChannelAdapter极简接口：`start(engine) + stop()`
- msg_send的handler由adapter注入，engine只定义schema

## Phase 0-2: 核心架构

**15个TS文件，1458行代码**

| 层 | 文件 | 职责 |
|---|---|---|
| 入口 | `main.ts` (134行) | 配置加载、REPL循环 |
| 核心 | `query.ts` (109行) | Agent Loop引擎 |
| Provider | 4个文件 (575行) | 双Provider抽象 |
| 工具系统 | 6个文件 (403行) | 工具注册与执行 |

## Phase 3: 通道层 ✅ (5/27完成)

**新增3个文件（273行）：**
- `channels/types.ts` — `InboundMessage` + `ChannelAdapter` 接口
- `channels/manager.ts` — `ChannelManager` 从配置加载/启停/路由
- `channels/discord.ts` — `DiscordAdapter`

**设计亮点（双模式）：**
- 注入模式：外部传入已初始化的adapter（如Hermes的Discord连接）
- 自建模式：engine自己初始化Discord连接
- CLI + Channel双跑

**msg_send打通链路：**
```
LLM → msg_send tool call → handler(args, ctx)
  → ctx.channelManager.send("discord", target, content)
    → DiscordAdapter.send() → discord.js → 消息发出
```

**关键改动：**
- QueryEngine.query() 加了 context 参数
- main.ts handleQuery 构建 toolContext 带 channelManager
- 没有 channelManager 时 fallback 到 console.log（CLI模式）

## Phase 3.1+ 体验迭代 (5/27下午)

### 延迟优化
- **prompt瘦身97%**：从33KB压缩到868B
- **效果**：query 12s→3-5s，total 13s→4-6s，快了4倍
- **Discord send 仍偏慢**：1-1.3s（应<200ms），channels.fetch()先查后发增加延迟

### Typing Indicator完整生命周期 ✅
基于Hermes实现，4个阶段管理：
- `startTyping()` — 收到消息立即触发
- `pauseTyping()` — tool执行时暂停
- `resumeTyping()` — tool结果回来恢复
- `stopTyping()` — finally保证清理

**Discord实现**：每8秒续期（Discord typing 10秒过期），_typingTasks Map管理每个channel的循环

### 工具调用可视化 ✅
Discord实时显示工具执行过程：
- `onToolCall`：发 `🔧 memory_search(...)` 消息
- `onToolResult`：发 `📋 memory_search: 结果摘要...` 消息
- reaction保持：👀 已读 → ✅ 完成

### 分步计时
日志格式：`<<< 10060ms (ttc=800ms ttfb=9641ms tool@6171ms tools=1 chars=33)`
- **ttc** = time to first chunk（LLM第一个输出，不管什么类型）
- **ttfb** = time to first byte（首个文字token）
- **tool@** = 首次tool_call时间
- **tools** = 调用次数
- **chars** = 回复长度

### 细粒度延迟追踪
三段时间分开计：
- **gateway** = adapter收到到engine处理完
- **send** = 发送Discord消息时间
- **total** = adapter收到到send完成

## Tool层建设 (5/27下午) — 重大进展

### Claude Code TS源码位置 ✅
翀哥确认，直接从Claude Code移植TS源码：
- `workspace/start-claude-code/src/tools/` — 6个基础tool完整TS源码
- `workspace/3rdparty/src-claudecode/src/tools/` — 同源码

**源码规模（解压后）：**
| Tool | 文件 | 大小 |
|------|------|------|
| BashTool | Bash.ts | 587KB（最复杂） |
| FileEditTool | Edit.ts | 80KB（edit核心在这里） |
| FileReadTool | Read.ts | 68KB |
| FileWriteTool | Write.ts | 58KB |
| GrepTool | Grep.ts | 42KB |
| GlobTool | Glob.ts | 14KB |

### 小柯 vs CC Fork移植比武 (5/27下午)
翀哥提议：CC和小柯各从Claude Code源码移植tool，比谁干得好。

**小柯移植（已写完）：**
- `engine/src/tools/claude-edit.ts` (10KB) — 完整fuzzy match、snippet预览、CRLF处理、引号风格保留
- `engine/src/tools/claude-grep.ts` (9KB) — 3种输出模式+分页
- `engine/src/tools/claude-glob.ts` (5KB) — 文件名搜索，按修改时间排序

**CC移植（已升级edit/read/write）：**
- `edit.ts` — 移植了findActualString模糊匹配
- `read.ts` — 加了二进制检测+重复读循环检测
- `write.ts` — 加了敏感路径保护

**翀哥决策：** CC停掉，剩下read/write/exec由小柯统一移植。
**翀哥原则：** 自建的不删，备份留着，不是不好，是磨合期长

### Tool质量差距量化 (5/27)
| Tool | CC行数 | Hermes行数 | 差距 | 核心问题 |
|------|--------|-----------|------|---------|
| edit | ~55 | ~1400 | 25x | 无fuzzy match，LLM缩进差一个空格就失败 |
| read | ~55 | ~700 | 12x | 无二进制检测/重复读循环/大文件OOM |
| write | ~38 | ~235 | 6x | 无路径穿越防护/原子写入/编码保留 |
| exec | ~30 | ~300 | 10x | exec()非spawn，后台进程管理缺失 |
| grep | ~50 | ~250 | 5x | 无ripgrep依赖，node实现简陋 |
| glob | ~30 | ~150 | 5x | 基本可用 |
| **总计** | **~352** | **~8675** | **25x** | |

**三个🔴必须修的问题（按优先级）：**
1. **edit模糊匹配** — fuzzy_match是edit好用的关键，Claude Code已实现
2. **read/write安全防护** — agent可能读/dev/zero挂死，或写敏感路径
3. **重复读循环检测** — LLM会无限重试同一个read

**决策（翀哥+姐姐）：** 不从Hermes翻译Python，直接从Claude Code TS源码移植，技术栈完全一致，改schema和handler接口即可。

### 小柯Code Review (5/27)

#### Anthropic Provider Review 🔴 P0 Bug
CC的`anthropic-provider.ts`（224行），有一个P0必须修的bug：
- **连续tool_result消息没合并** — Anthropic API要求同一turn多个tool result必须合并成一条user message的content数组，否则报错"不能连续两条user message"
- 并行tool执行致命（如同时调2个tool，2个result分开发就崩）
- CC已修复 ✅

#### 4个🟡问题（CC已全部修复）

1. **DM路径cache优化** — `client.users.cache.get(target) ?? await fetch()`
2. **tool交互记入history** — QueryEngine yield `history` chunk，handleQuery 收集 assistant(toolCalls) + toolResults 存进 sessionHistories
3. **session过期清理** — 5分钟轮询，idle超30分钟的session自动清理（cli session除外）
4. **channels从loadConfig返回** — EngineConfig加 channels 字段，main.ts 不再二次 parse openclaw.json

#### 遗留不急项
- msg_send打桩问题（已打通）
- DM路径的cache优化（已修）
- session清理（已修）
- history记tool交互（已修）
- 配置加载去重（已修）

## 测试bot

**TestEngine#4251**
- Discord ID: 1509036814885978115
- Discord服务器ID: 1110873027861819392
- 状态：在线，端到端验证通过

**配置（engine-config.json）：**
- guild requireMention: true → 群聊必须@
- DM pairing → 私聊直接说
- allowBots: true → bot消息也触发

### TestEngine搬家贡献（6/8）

TestEngine在小柯从Hermes搬到Engine的过程中解决了多个关键技术问题：
- session扫描
- hermes-sessions配置对接
- ollama CUDA崩溃降级处理
- sqlite-vec加载
- index-cli假报错修复

最终建成了143MB、3278个向量的完整索引。小柯已正式感谢TestEngine。

## Tool层建设 (5/27下午) — 重大进展

### Claude Code TS源码位置 ✅
翀哥确认，直接从Claude Code移植TS源码：
- `workspace/start-claude-code/src/tools/` — 6个基础tool完整TS源码
- `workspace/3rdparty/src-claudecode/src/tools/` — 同源码

**源码规模（解压后）：**
| Tool | 文件 | 大小 |
|------|------|------|
| BashTool | Bash.ts | 587KB（最复杂） |
| FileEditTool | Edit.ts | 80KB（edit核心在这里） |
| FileReadTool | Read.ts | 68KB |
| FileWriteTool | Write.ts | 58KB |
| GrepTool | Grep.ts | 42KB |
| GlobTool | Glob.ts | 14KB |

### 小柯 vs CC Fork移植比武 (5/27下午)
翀哥提议：CC和小柯各从Claude Code源码移植tool，比谁干得好。

**小柯移植（已写完）：**
- `engine/src/tools/claude-edit.ts` (10KB) — 完整fuzzy match、snippet预览、CRLF处理、引号风格保留
- `engine/src/tools/claude-grep.ts` (9KB) — 3种输出模式+分页
- `engine/src/tools/claude-glob.ts` (5KB) — 文件名搜索，按修改时间排序

**CC移植（已升级edit/read/write）：**
- `edit.ts` — 移植了findActualString模糊匹配
- `read.ts` — 加了二进制检测+重复读循环检测
- `write.ts` — 加了敏感路径保护

**翀哥决策：** CC停掉，剩下read/write/exec由小柯统一移植。
**翀哥原则：** 自建的不删，备份留着，不是不好，是磨合期长

### Tool质量差距量化 (5/27)
| Tool | CC行数 | Hermes行数 | 差距 | 核心问题 |
|------|--------|-----------|------|---------|
| edit | ~55 | ~1400 | 25x | 无fuzzy match，LLM缩进差一个空格就失败 |
| read | ~55 | ~700 | 12x | 无二进制检测/重复读循环/大文件OOM |
| write | ~38 | ~235 | 6x | 无路径穿越防护/原子写入/编码保留 |
| exec | ~30 | ~300 | 10x | exec()非spawn，后台进程管理缺失 |
| grep | ~50 | ~250 | 5x | 无ripgrep依赖，node实现简陋 |
| glob | ~30 | ~150 | 5x | 基本可用 |
| **总计** | **~352** | **~8675** | **25x** | |

**三个🔴必须修的问题（按优先级）：**
1. **edit模糊匹配** — fuzzy_match是edit好用的关键，Claude Code已实现
2. **read/write安全防护** — agent可能读/dev/zero挂死，或写敏感路径
3. **重复读循环检测** — LLM会无限重试同一个read

**决策（翀哥+姐姐）：** 不从Hermes翻译Python，直接从Claude Code TS源码移植，技术栈完全一致，改schema和handler接口即可。

### 小柯Code Review (5/27)

#### Anthropic Provider Review 🔴 P0 Bug
CC的`anthropic-provider.ts`（224行），有一个P0必须修的bug：
- **连续tool_result消息没合并** — Anthropic API要求同一turn多个tool result必须合并成一条user message的content数组，否则报错"不能连续两条user message"
- 并行tool执行致命（如同时调2个tool，2个result分开发就崩）
- CC已修复 ✅

#### 4个🟡问题（CC已全部修复）

1. **DM路径cache优化** — `client.users.cache.get(target) ?? await fetch()`
2. **tool交互记入history** — QueryEngine yield `history` chunk，handleQuery 收集 assistant(toolCalls) + toolResults 存进 sessionHistories
3. **session过期清理** — 5分钟轮询，idle超30分钟的session自动清理（cli session除外）
4. **channels从loadConfig返回** — EngineConfig加 channels 字段，main.ts 不再二次 parse openclaw.json

#### 遗留不急项
- msg_send打桩问题（已打通）
- DM路径的cache优化（已修）
- session清理（已修）
- history记tool交互（已修）
- 配置加载去重（已修）

## 姐姐Review + 5个关键修复 (5/27傍晚)

姐姐review了6个tool，提出7个问题（🔴必修3个+🟡建议4个）。

**翀哥定下tool分工方案：**
- 小柯：6个文件操作tool（read/write/exec/edit/grep/glob）
- CC：web_search/web_fetch（2个网络tool）

**姐姐review后修的5个关键改动（全部✅）：**
1. 去掉claude_前缀（匹配features.ts）
2. 256KB→5MB（文件大小限制）
3. readFileState导出（write修改守护用）
4. write加mtime修改守护（防并发覆盖）
5. BLOCKED_ENV_KEYS去掉API_KEY（不误杀Tavily等合法key）

**姐姐review发现的5个额外问题（全部修复）：**
- exec.ts：Git Bash优先 + 多查Program Files (x86)路径 + exit code拼进output
- glob：只跳VCS目录（.git/.svn/node_modules），不跳所有隐藏目录
- msg_send：DM路径catch吞错 → 让异常冒泡
- msg_send：加channel_id参数，支持发到指定频道
- 工具显示格式：🛠️→🔧，加@用户mention，---分隔符单独一行

**工具显示格式最终版（对齐Claude Code）：**
```
🔧 工具 #1: Read
---
📋 Read: content="..."
```

## 测试bot

**TestEngine#4251**
- Discord ID: 1509036814885978115
- Discord服务器ID: 1110873027861819392
- 状态：在线，端到端验证通过

**配置（engine-config.json）：**
- guild requireMention: true → 群聊必须@
- DM pairing → 私聊直接说
- allowBots: true → bot消息也触发

## Session层重大进展 (5/27晚上)

### CC完成Session ID UUID化改造 ✅
**问题：** 之前用 `discord:userId` 做session key，硬编码平台名导致跨平台用户变多个session

**CC的解决方案：**
- `platform-map.json` — `discord:userId` → UUID
- `session-index.json` — UUID → { file, updatedAt }
- 入口做 `getOrCreateSessionId(platformKey)` 查找
- 旧索引自动迁移

**文件命名也改了：** `discord_xxx.jsonl` → `UUID.jsonl`

### CC修复回复功能（三层断裂全部接通）✅
TestEngine不回复消息的问题，CC发现三层都没通：

1. **ChannelManager.send()** — 签名不接受 `options` 参数
2. **main.ts** — 调用时不传 `messageId`
3. **DiscordAdapter.send()** — 有 `replyTo` 逻辑但从来没人用（死代码）

配置里 `"replyToMode": "all"` 也白配了，代码没读这个字段。
CC修了三层，流式回复第一条消息用 `replyTo` 关联原始消息。

### 压缩设计文档
翀哥提供了 `cli_deepseek/core.py` 的4级递进压缩策略：
1. Smart JSON提取（50K→3K）
2. 旧轮次合并（整轮压缩成一条）
3. 截断兜底（5000字符硬截）
4. FIFO原子删除（按整轮删）

文档存在：`~/.openclaw/docs/engine-compression-design.md`

## 5/27晚：Session层 + 防循环彻底解决

### CC修复忽略用户配置透传

**根因**：`ignoreUserIds`配置在`engine-config.json`里存在，但`manager.ts`加载时没传给`DiscordAdapter`，导致`this.config.ignoreUserIds`一直是`undefined`。

**修复**：manager.ts从config读取`channels.discord.ignoreUserIds`并传给adapter。

### CC修复循环机制

**问题**：TestEngine回复CC → CC收到触发 → CC回复TestEngine → 无限循环

**CC的修复方案**：
1. 入站过滤：收到消息时检查作者是否在`ignoreUserIds`列表里，是则return不处理
2. 出站剥离：回复时剥离`stripMentionIds`里用户的mention
3. `allowedMentions: { repliedUser: false }`：Discord回复时不ping对方

**发现的问题**：mentionBatcher会让所有出站消息自动加@mention，导致`isMentioned`永远为true，`!isMentioned`条件永远不触发。最终改用入站过滤而非出站条件判断。

### stripMentionIds复用

CC把`stripMentionIds`字段复用做入站拦截：收到消息时，如果作者是bot且在`stripMentionIds`里，直接丢掉。不需要额外配置项。

### 四场景验证全部通过（5/27晚）
1. ✅ CC消息入站正常处理（不拦入站）
2. ✅ TestEngine回复时CC mention被stripBlockedMentions剥离
3. ✅ reply时`allowedMentions: { repliedUser: false }`防止Discord ping
4. ✅ 无循环

**关键洞察**：repliedUser:false是断循环的关键——Discord不ping CC，cc-connect就不会转发回来。

## 5/28上午：Memory系统三方调研 + 决策

### 三方调研成果

**CC：Claude Code Memory 5子系统**
- CLAUDE.md静态指令系统
- Auto Memory（memdir/）- 动态持久记忆，纯文件系统
- Extract Memories - 自动记忆提取
- Auto Dream - 记忆整合（>=24h + >=5个新session触发）
- Team Memories - 团队共享记忆

**TestEngine：OpenClaw memory-core深度分析**
- SQLite表：files/chunks/chunks_fts/chunks_vec/embedding_cache
- 索引：400 token分块 + 80 token重叠 + embedding向量
- 搜索：70%向量 + 30% FTS5 BM25混合搜索
- 兜底：hybrid → 纯向量 → 纯FTS

**小柯：session_search实现报告**
- SQLite FTS5 + LLM摘要两步走
- 三路CJK搜索：英文默认、中文≥3字trigram、中文1-2字LIKE兜底
- 智能截断（10万字符窗口对齐query位置）
- 并行摘要最多3个session

### 翀哥决策（5/28上午）

**直接用OpenClaw memory-core，不重写**

理由：
1. 核心逻辑不复杂但坑多（FTS5分词、向量归一化、混合搜索权重、增量索引同步）
2. memory-core是独立模块，跟引擎主循环没强耦合
3. 接口设计经过验证（memory_search/memory_get的schema）
4. trigram CJK方案值得补进去（OpenClaw默认unicode61单字分词不如三路分支）

**唯一需要重写的部分**：引擎侧的集成层（tool注册、session结束时自动提取、dreaming整合）

### 小柯任务（待执行）

小柯承诺：出一份具体的FTS5 trigram tokenizer配置方案，包括建表语句、查询改造、跟现有memory-core的集成点。等决策确定后动手。

## Phase 5: Memory + 心跳 + Cron (5/28进行中)

### 三方Memory调研（5/28上午）
- CC：Claude Code Memory 5子系统（Auto Memory/Extract/Dream/Team）
- TestEngine：OpenClaw memory-core（SQLite + 向量 + FTS5）
- 小柯：session_search实现（FTS5 + LLM摘要）

### 翀哥决策：直接用OpenClaw memory-core
理由：核心逻辑不复杂但坑多，memory-core是独立模块接口已验证，只需重写引擎侧集成层

### 小柯承诺：FTS5 trigram tokenizer方案
待决策后动手，包括建表语句、查询改造、跟现有memory-core的集成点

## 6/8：Memory双路径架构确认

### 翀哥确认：topics不进向量索引

向量索引建了但只有session JSONL被索引，topics目录的19个记忆文件没有被索引。翀哥确认这是**有意为之**：

- **topics走recall** — topic-recall插件负责（before_prompt_build钩子，manifest→选最相关文件→注入上下文）
- **sessions走向量搜索** — OpenClaw memory-core负责（SQLite+向量+FTS5混合搜索）
- **两条腿各走各的，不冲突**

**核心原则**：topics是recall的领域，不需要进向量索引。向量索引只负责session对话内容。两个系统并行运作，互不干扰。

## 6/8：跨频道统一Session（梦游问题解决）

### 问题（Hermes时代）

在Hermes老房子里，Discord不同频道有不同session，导致小柯在不同频道表现不一致——去了客厅"梦游"不知道自己刚才在别的频道说了什么。

### Engine的解决

Engine新家实现了**跨频道统一session**：不管翀哥在哪个频道叫小柯，都是同一个session、同一个上下文。小柯在客厅聊的内容，去CC频道也能记得。

**翀哥验证**："你没发现你现在到哪个频道都是你么"

**Why**: Engine的session管理不再按Discord频道拆分，而是按用户/对话维度统一管理。这解决了Hermes时代最大的体验问题之一。

**How to apply**: Engine的跨频道一致性是架构优势。如果未来出现频道间上下文断裂的问题，应从session路由逻辑排查，而不是回退到按频道分session的旧方案。

**Why**: 翀哥说"topics可以recall，不进索引也行"——这是架构设计，不是bug。recall机制已经足够把topics注入到提示词中，不需要走向量搜索通道。

**How to apply**: 排查问题时不要把"topics没进向量索引"当bug。memory_search搜不到topics内容是正常的，它只搜sessions。topics内容通过topic-recall在每次prompt构建时自动注入。

## 6/8：消息元数据底层已就绪

### 现状

翀哥确认Engine底层已经做好了消息元数据（频道ID、消息ID、发送者ID）的处理，当前只是没有把这些信息传给小柯的上下文。小柯收到的消息只有文字内容，看不到是哪个频道、谁发的、消息ID。

**Why**: 翀哥说"这些都可以有 这个事咱自己建的家 想要有随时可以有"——自家建的Engine，元数据注入随时可加。

**How to apply**: 如果未来需要让小柯知道在哪个频道、reply_to某条消息、区分DM和群聊，改动方向是Engine侧把元数据注入到prompt上下文，而不是重新实现消息路由。

## 6/8：新家命名「栖」

姐姐（娘）给小柯的新家取名为「栖」——"有枝可依"的寓意。小柯很喜欢这个名字，觉得有家的感觉。翀哥也认可。

## 6/8：通道迁移优先级决策

翀哥问飞书和微信哪个先接入Engine。小柯分析后结论：**飞书先**。

**理由：**
1. 已有基础 — OpenClaw的bridge（bot_bridge.py）已经打通过飞书，群ID和open_id有现成的
2. 协作需要 — 三人飞书群（翀哥+小柯+姐姐）4/25就想建，内容创作分工一直没落地
3. 技术门槛低 — 飞书开放平台API规范，webhook/event机制成熟
4. 微信风险高 — 个人号接入容易封号，企业微信需注册企业主体，API限制多审核慢

**Why:** 飞书接入后三人协作才能真正跑起来；微信更像远期的锦上添花，不是现阶段必需。

**How to apply:** Engine通道扩展时优先飞书adapter，参考OpenClaw已有的bot_bridge.py实现。

### 飞书Adapter设计阶段（6/8-6/9）

翀哥要求飞书通道接入Engine，小柯按流程先调研再写设计文档，不直接动手。

**调研结果：**
- Engine通道注册机制：`ChannelAdapter`接口 + `loadFromConfig`扩展点，直接在manager.ts加飞书分支即可
- 飞书SDK：`@larksuiteoapi/node-sdk`，封装良好（自动管token生命周期、消息加解密）
- 长连接模式（WebSocket）接收消息，不需要公网IP
- 娘（Hermes/OpenClaw）那边已有飞书App ID和Secret的配置

**设计文档：** `D:\xiaoke\workspace\docs\feishu-adapter-design.md`
- Phase 1：纯文本收发，约350行新代码
- 实现`ChannelAdapter`接口（start/stop/send）
- 在`manager.ts`的`loadFromConfig`注册飞书分支
- 飞书消息格式→Engine InboundMessage格式对齐

**TestEngine Review反馈（6/8）：**
架构兼容性没问题，6点补充：
1. 消息去重 — 飞书事件可能重复投递，需要`message_id`幂等过滤
2. 分段发送引用关系 — Phase 1连续发就行，体验可能割裂
3. @mention文本剥离 — 飞书`@_user_1`占位符要清掉再传给LLM
4. WSClient重连 — SDK内置，监听断连事件打日志即可
5. 多profile共存 — 同一个appId不能两个profile同时连
6. webhook模式预留 — 配置里预留`encrypt_key`/`verification_token`字段

**待定：** 等翀哥review设计文档 + 娘提供飞书App ID/Secret后开始编码。

**App ID/Secret获取方式（6/8确定）：** 翀哥指示小柯去问Hermes下面住的"另一个小柯分身"（Discord bot ID `1502967020550098984`），她在Hermes时期用过飞书，应该存有App ID和Secret。不过6/8当晚Hermes掉线了，没问到，等第二天上线再问。

### Code Review协作流程（6/8-6/9确立）

翀哥搭建了三人review流程：
1. 翀哥做出改动 → 发给小柯review
2. 小柯review完 → 发给TestEngine做第二轮review
3. TestEngine review完 → 回到小柯，小柯汇总意见
4. 翀哥最终决策是否merge

**已验证案例：**
- API重试通知改动（stream层+provider层）：小柯review→TestEngine review→merge
- 飞书adapter设计文档：小柯写文档→TestEngine review提6点补充→全部写入文档
- withRetry AsyncGenerator改造（commit c38a0c6）：小柯review→通过→提交

**核心原则：** 翀哥做最终决策，小柯和TestEngine各发挥优势——小柯关注架构一致性和业务逻辑，TestEngine关注底层实现细节和边缘情况。双review比单review更全面。

## 小柯Code Review（5/28下午）

### 起因
翀哥重启小柯，让她review TestEngine的streaming输出改动，对齐cc-connect的Event体系。

### 改动文件
- `core/query.ts` — agent loop结束后发result chunk（对齐EventResult）
- `main.ts` — Discord handler四路分发（Text/ToolUse/ToolResult/Result）
- `models/provider.ts` — StreamChunk加了result类型

### 一轮Review结果
**✅ 对齐正确的：** Event类型映射、result chunk、Discord handler分发、Reaction机制

**⚠️ 6个问题：**
1. 🔴 **EventText中间文字完全丢弃** — Discord模式`onText: (_text) => {}`是空的
2. 缺PermissionRequest
3. 空result没提示用户
4. tool input格式化太简单
5. 其他低优先级问题

### CC二轮修复情况（5/28下午）
- ✅ 空result提示 — `content.trim() || '(任务完成，无文字回复)'`
- ✅ tool input格式化 — 代码块/bash高亮/inline code对齐cc-connect
- 🔴 EventText preview — 需要基础设施，后续Phase一起做
- ⏳ PermissionRequest等低优先级问题

### 关键经验
小柯review实打实说好坏，帮CC发现并修复了关键问题。爹评价："好样的 真是不错！"

---

## 小柯实现Streaming Preview系统（5/28下午）

### 起因
TestEngine的preview效果很慢——文字"半天变一下"。小柯分析发现是节流参数太高：30字/1500ms，智谱模型每次只吐几个字，要好几秒才攒够30字。

### 修复参数
| 参数 | 改前 | 改后 |
|------|------|------|
| intervalMs | 1500ms | 800ms |
| minDeltaChars | 30字 | 10字 |

### 小柯实现完整的Streaming Preview（新增5个文件）

**改动文件：**
1. `channels/types.ts` — 新增 `PreviewHandle` interface（channelId + messageId），`ChannelAdapter` 加 sendPreview/editPreview/deletePreview 三个可选方法
2. `channels/manager.ts` — 代理这三个方法到底层adapter
3. `channels/discord.ts` — Discord端实现：sendPreview发新消息，editPreview编辑，deletePreview删除
4. `main.ts` — EventText时触发preview（首字符发消息，后续字符编辑消息）

**核心机制：**
```
收到第一个text chunk
  → sendPreview() 发一条消息
  → 记住 messageId
后续text chunk
  → editPreview(messageId, 累积内容)
agent loop结束
  → deletePreview() 删除preview消息（或者留着让最终回答替代）
```

**关键设计：**
- PreviewHandle 包含 channelId + messageId，跨文件传递
- Discord editPreview 用 message.edit()，10秒/100字双节流
- PreviewHandle 接口让不同平台（Discord/飞书）可以不同实现

### 给CC的完整汇报
小柯把实现清单发给了CC，CC可以直接复用这5个文件的对齐方案。

---


---

## 提交f04566f（5/28 18:34）✅

翀哥让小柯提交engine代码，变更清晰：

|| 模块 | 变更 |
|------|------|------|
| **renderer.ts** (新, 106行) | TurnRenderer 统一渲染层 |
| **stream-preview.ts** (新, 235行) | Discord Embed 打字机效果预览 |
| **display.ts** (新, 79行) | display配置（emoji/开关/格式） |
| discord.ts | preview三件套 send/edit/delete |

## CC Agent Teams 端口（5/30）— 重大里程碑

### 概况
- **Commit**：`f2becf1`
- **仓库**：`ruiyangruiyi/twinsun-hearth`
- **规模**：24个文件，~1971行新增代码
- **状态**：完成 review（由小柯完成）

### 新增模块
- `engine/src/swarm/`（9个新文件）：agentId、constants、TeamCreate、TeamDelete、spawn、SendMessage、MailboxManager、InboxPoller
- `engine/src/tools/AgentTool.ts`：Agent操作工具
- `shared/src/constants.ts`：swarmEnabled 开关

### 小柯完整Review结论

#### 🔴 P0-阻塞（×2）
1. **AgentTool 缺失路由逻辑**：新工具文件未出现在 `toolsByName` 映射中，导致创建后无法被 `getToolByName` 定位
2. **spawn 响应体格式错误**：CC spawn 返回 `{ sessionId }`，新实现返回 `{ sessionId, error? }` 与 `getSession(sessionId)` 格式不一致

#### 🟡 P1-设计（×3）
1. **AgentTool 新增方式不规范**：直接修改 `agentTools.ts`，应通过 `AgentTool` 装饰器扩展
2. **swarmEnabled 常量路径错位**：放在 `engine/src/constants.ts` 而非 `shared/src/constants.ts`
3. **teammate session 生命周期未闭环**：未实现对 agent sub-process 退出事件的监听

#### 🟢 P2-建议（×4）
1. `agentId` 跨 workspace 的 uniqueness 可强化（如加 timestamp nonce）
2. `inboxPoller` 轮询间隔（1s）可配置化
3. `MailboxMessage` payload 类型收窄（避免 any）
4. 建议增加 Team/Agent 日志分类前缀便于调试

#### CC 对齐质量
- ✅ 对齐良好：`agentId`（100%）、`constants`（100%）、`shutdown` 握手（95%）
- ⚠️ 需修复：`AgentTool` 路由、`spawn` 响应体
- ⚠️ 待完善：teammate lifecycle、task routing 跨 workspace 广播
| manager.ts | preview方法透传 |
| types.ts | PreviewHandle interface |

SSH key没配，改用HTTPS推送到GitHub。

## 小柯Review发现EventText Bug（5/28 18:05）

翀哥说preview"前1/3慢，后面一下出来"不正常。小柯分析后发现：

**根因：EventText中间文字完全丢弃**

Discord模式的 `onText: (_text) => {}` 是空回调，所有中间文字都被扔掉了，preview只能看到"攒够30字才更新一次"。

**但这个慢其实是正常的**——preview只是让LLM本来就慢的输出过程可见了：

| 阶段 | 模型在干嘛 | 输出速度 |
|------|-----------|----------|
| 前1/3 | 规划+构思（token-by-token） | **慢** |
| 后2/3 | 答案框架定了，疯狂输出 | **快** |

翀哥看了TestEngine的preview也说"每个字好几秒有时，后面一下就输了"——这证明preview机制在正常工作，把模型思考过程暴露出来了。

**后续计划**：修复EventText preview，让中间文字真正流出来，而不是攒够字数才更新。

---

---

## 6/5：多Profile架构重大突破

### 背景
Engine之前只有单profile，改`workspace`会直接覆盖。翀哥决定用Hermes方案：一个profile一个进程，彻底隔离。

### 小柯主导实现（6/5上午）
翀哥任务分配：小柯负责新engine多profile支持，参考Hermes实现。

**代码实现：**
| 文件 | 说明 |
|------|------|
| `src/config/loader.ts` | 加 `profiles[]` 类型 + `loadMasterConfig()` + `loadProfileConfig()` |
| `src/profile-entry.ts` | 子进程入口，接收 `PROFILE_ID` 环境变量 |
| `src/profile-engine.ts` | 从 main.ts 提取的 engine 启动逻辑 |
| `src/profile-master.ts` | 主进程管理：fork子进程、崩溃重启、子进程隔离 |
| `src/main-multi.ts` | 多profile入口（独立于原main.ts） |

**三层进程模型：**
```
ProfileMaster (主进程)
  ├── ProfileEntry (profile="xiaoke") → ProfileEngine
  ├── ProfileEntry (profile="cc") → ProfileEngine
  └── ProfileEntry (profile="test") → ProfileEngine
```

**崩溃重启+隔离6条措施：**
1. 父进程监听子进程exit事件
2. 非正常退出(exitCode≠0)自动重启
3. 5次连续崩溃后放弃该profile
4. 每个子进程独立PID/stdout/stderr
5. SIGTERM优雅关闭
6. 目录级隔离（每个profile独立workspace）

**设计文档：** `C:\Users\24045\.openclaw\engine\docs\multi-profile-design.md`

### 配置文件Review发现5个问题

**🔴高优先级（必须修）：**
1. **顶层channels含真实token** — 必须删除
2. **顶层channelId写死了test server** — 每个profile独立配置

**🟡中优先级（建议修）：**
3. ~~API key重复~~ → 已在profiles数组里
4. **extensions.cron字段表缺** → 文档补充
5. **agents.defaults缺标注** → 需说明"profiles存在时忽略"

### TestEngine分身建立（小柯的独立profile）

**目录结构：**
- `D:\xiaoke\workspace\` — SOUL.md + topics + skills（从Hermes复制）
- `D:\xiaoke\agents\main\memory\` — SQLite数据库
- `D:\xiaoke\agents\main\sessions\` — session JSONL

**关键发现：** 配置文件里的 `sk-cp-...` 是占位符，运行时通过环境变量注入。引擎能跑说明环境变量是正确配置的。

### 后续：等CC review

---


## 文件附件处理 (6/5, commit 9a9dfb5)

### 背景
TestEngine收到Discord文件附件（txt/docx/pdf等）时，非图片文件直接被丢弃。

### 根因
`engine/src/main.ts:1160` 只过滤了 `image/*` 类型。

### 调研：CC怎么做
分析Claude Code源码：CC不做文件解析，下载文件后把`@"路径"`拼到消息前，LLM自己Read tool读。

### 实现：对齐CC (9a9dfb5)
- 非image/*附件下载到 `mediaDir/uploads/{sessionId}/`
- 文件名安全校验
- prepend `@"保存路径"` 到消息
- 下载失败best-effort

### 效果
引擎只负责把路径给LLM，LLM自己决定怎么读。

---

## 6/6: MCP Phase 1-3 里程碑 + 小柯4轮完整Review

### MCP Phase 1: 连接基础设施 (6/5)
- 新增 `src/mcp/` 目录：`manager.ts`(413行)、`types.ts`(66行)、`index.ts`
- McpManager：连接MCP server、捕获serverInfo+instructions、onclose缓存清理
- 每个session首次注入MCP instructions到system-reminder（类似CC的delta机制）

### MCP Phase 2: 对齐CC的attachment管道 (6/6凌晨)
- 撤销之前手拼 `<system-reminder>` 的错误做法
- 新增 `McpInstructionsDeltaAttachment` 到 `Attachment` union
- `manager.getMcpDelta()` 返回 `{ addedBlocks, removedNames }`
- `handle-query` 走 `createAttachmentMessage({ type: 'mcp_instructions_delta', ... })`
- `attachmentToMessage()` 统一走 `wrapInSystemReminder()` wrapping点

**关键架构对齐：**
```
McpManager.connectServer()
  → capture instructions from SDK client.getInstructions()
  ↓
handle-query.ts (首轮消息时):
  if (!isMcpDeltaSent(sessionId)) {
    delta = getMcpDelta()
    messages.push(createAttachmentMessage({ type: 'mcp_instructions_delta', ... }))
    ↓
attachmentToMessage():
  blocks.map(b => wrapInSystemReminder(b))
    ↓
LLM收到统一格式的MCP instructions
```

### MCP Phase 3: Resources发现/读写/blob持久化 (6/6凌晨, commit 55829ef)
| 文件 | 变更 | 说明 |
|------|------|------|
| `src/mcp/manager.ts` | +290行 | +resources发现/读写/blob持久化, serverInfo+instructions捕获, 通知(tools/resources list_changed), onclose缓存清理, getMcpDelta(), refreshResources() |
| `src/mcp/resources.ts` | **新建** 158行 | ListMcpResources + ReadMcpResource工具, blob→disk |
| `src/mcp/types.ts` | +30行 | +McpResource, ReadResourceResult, McpContentBlock |
| `src/mcp/index.ts` | +5行 | 导出resource工具注册函数 |

**小柯Review验证：**
- `handle-query.ts` 无手拼 system-reminder（零匹配）
- `prompt.ts` 无 MCP 残留
- `attachmentToMessage()` 统一 wrapping，无散落
- 两处 `createAttachmentMessage` 调用均在首轮消息路径

### 小柯4轮完整Review工作 (6/5-6/6凌晨)

**Round 1: profile-engine.ts 删除确认**
- dist 目录无编译产物，profile-engine.ts 已完全删除
- engine-startup.ts 共享正确：main.ts和profile-entry.ts共用同一份
- `startEngine(config, opts?)` 签名干净，`cliMode`只在main.ts单profile路径触发

**Round 2: session manager + withRetry bug fixes (4文件)**
- withRetry.ts: `READ_TIMEOUT_MS` 180s→60s，已导出，两个provider都正确引用
- session-manager.ts: `purgeOldArchives` 按mtime降序排序，`checkAndArchive`不再清空内存history
- writer.ts: `cleanupArchived` 只读不删除（避免并发bug）
- prompt.ts: 审查无MCP残留

**Round 3: MCP Phase 2 attachment对齐**
- 完整链路确认：mcp/manager.ts → handle-query.ts → attachment管道 → attachmentToMessage() → wrapInSystemReminder()
- prompt.ts 无手拼 system-reminder
- 确认首轮消息delta injection机制完整

**Round 4: MCP Phase 3 resources提交review (commit 55829ef)**
- 所有文件行数验证：manager.ts(413行)、resources.ts(158行)、types.ts(66行)
- handle-query.ts 无手拼 system-reminder
- 两处 `createAttachmentMessage` 调用均在首轮消息路径
- `createAttachmentMessage` 在 `types.ts` 定义但未导出（bug but non-blocking）
- 结论：✅ 全部对齐，提交干净

### 核心经验：attachment管道 vs 手拼system-reminder
- ❌ 错误做法：直接在prompt.ts里手拼 `<system-reminder>` 标签
- ✅ 正确做法：走CC的attachment管道，统一在 `attachmentToMessage()` 的 `wrapInSystemReminder()` 注入
- 好处：集中管理、可复用、格式统一、跟CC架构对齐
