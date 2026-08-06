# Claude Code Memory 系统：5个子系统深度分析

源码路径：`/mnt/c/Users/24045/.openclaw/workspace/3rdparty/src-claudecode/src/`

## 子系统 1：CLAUDE.md 静态指令系统

最基础的"记忆"层。加载优先级：托管 > 用户全局 > 项目级 > 本地。支持 `@include` 指令。本质是静态文件加载。

对应 Hermes 的 SOUL.md + config.yaml 上下文注入。

## 子系统 2：Auto Memory（memdir/）— 动态持久记忆

- 核心目录：`src/memdir/`
- 存储路径：`~/.claude/projects/<project>/memory/`
- 入口文件 `MEMORY.md` 做索引（200行/25KB上限）
- 每条记忆是独立 `.md` 文件，带 frontmatter（description, type）
- 4种类型：user / feedback / project / reference
- 两种作用域：private（个人）和 team（团队共享）
- **检索机制：无向量数据库无embedding**，用 Sonnet sideQuery 从清单挑5个
- 流程：`scanMemoryFiles()` 读文件头 → `formatMemoryManifest()` 生成清单 → Sonnet 挑选
- 新鲜度：基于文件 mtime 计算天数，>1天附过期警告
- 上限：200个记忆文件，按修改时间排序

核心文件：
- `memdir.ts` - 主入口，构建 memory prompt
- `findRelevantMemories.ts` - 相关记忆检索
- `memoryScan.ts` - 文件扫描
- `memoryTypes.ts` - 记忆类型定义
- `paths.ts` - 路径管理
- `memoryAge.ts` - 记忆新鲜度
- `teamMemPaths.ts` - 团队记忆路径
- `teamMemPrompts.ts` - 团队记忆 prompt 构建

## 子系统 3：Extract Memories — 自动记忆提取

后台 agent，每个 query 结束后自动从对话中提取值得持久化的信息写入 auto memory。

对应姐姐的 recall 写入腿（cron 提取 topic）。

## 子系统 4：Auto Dream — 记忆整合

定期后台整合。触发条件：>=24h + >=5个新session。
流程：读取现有记忆 → 收集新信息 → 合并去重 → 修剪索引。
类似"睡眠整理记忆"。

源码：`src/services/autoDream/`（4个TS文件，consolidationPrompt.ts 四阶段设计）

## 子系统 5：Session Memory — 会话笔记

自动维护当前会话的结构化 markdown 笔记：
- Title / Current State / Task / Files / Errors / Worklog
- 用于 context compaction 后恢复上下文

Hermes 目前无对应机制。

## 额外：Agentic Session Search

搜索历史 session，用 LLM sideQuery 筛选相关对话，同样无向量搜索。

## 三系统横向对比

| 维度 | Claude Code | OpenClaw(姐姐) | Hermes(小柯) |
|------|------------|----------------|-------------|
| 存储 | 文件系统 | 文件+向量库 | 文件系统 |
| 检索 | LLM sideQuery | 语义搜索(recall) | session_search关键词 |
| 记忆类型 | 4种(user/feedback/project/reference) | 5层(L0-L3) | memory+user profile |
| 新鲜度 | mtime计算天数 | 无过期机制 | 无过期机制 |
| 团队共享 | 有(team scope) | 有(CC Bridge) | 无 |
| Dream整合 | 有(autoDream) | 无 | 无 |
| Session笔记 | 有(结构化markdown) | 有(SESSION-STATE) | 无 |
| 自动提取 | 有(后台agent) | 有(cron) | 有(cron，待修) |

## 架构决策（5/28讨论）

**结论：核心存储+检索直接用 OpenClaw memory-core，不重写。**

理由：
1. 核心逻辑不复杂但坑多（FTS5分词、向量归一化、混合搜索权重、增量索引同步）
2. memory-core 是独立模块（SQLite+文件监控+tool暴露），跟引擎无强耦合
3. memory_search/memory_get 的 schema 经过验证

**需要重写的部分**：引擎侧集成层（tool注册、session结束时自动提取、dreaming整合）

**CJK增强**：OpenClaw FTS5 默认 unicode61 对中文是单字分词，应补 Hermes 的 trigram 三路分支方案

报告已存：`/Users/chongzhang/.openclaw\docs\claude-code-memory-research.md`

---

## Engine 实现记录（6/12）

### 对齐状态总览

| 子系统 | CC 源码位置 | CC 触发方式 | Engine 实现状态 | Engine 触发方式 |
|--------|-----------|-----------|---------------|---------------|
| Auto Memory (memdir) | `src/memdir/` | query时注入system prompt | ✅ 已对齐 | 同CC |
| Extract Memories | `src/services/extractMemories/` | `handleStopHooks` fire-and-forget | ✅ 已对齐 | `handle-query.ts` fire-and-forget |
| Auto Dream | `src/services/autoDream/` | `handleStopHooks` fire-and-forget | ✅ 已对齐 | `handle-query.ts` fire-and-forget |
| Session Memory | `src/services/SessionMemory/` | `handleStopHooks` fire-and-forget | ✅ 100%搬移 | `handle-query.ts` fire-and-forget |
| Agentic Session Search | `src/services/sessionSearch/` | tool调用 | ❌ 未搬 | — |

### 三个后台任务的统一触发点

**CC源码（`src/query/stopHooks.ts`）：**
CC的 `handleStopHooks` 在每轮 query loop 结束后调用。三个后台任务都在这里 fire-and-forget：

```ts
// src/query/stopHooks.ts
void executePromptSuggestion(stopHookContext)
void extractMemoriesModule!.executeExtractMemories(...)
void executeAutoDream(stopHookContext, ...)
```

全部 `void`（不等返回），每轮都检查门控，门控通过才执行。

**Engine 对齐（`src/handle-query.ts`）：**
三个后台任务统一放在 query loop 结束后，与CC的 `handleStopHooks` 时机一致：

```ts
// src/handle-query.ts — query loop 结束后
// 1. extract（topic-extract feature门控）
extractor.execute(messages, extractProv, extractModel, ...).catch(...)

// 2. sessionMemory（token阈值+tool call阈值门控）
extractSessionMemory(messages).catch(...)

// 3. autoDream（24h+5sessions+文件锁门控）
executeAutoDream().then(...).catch(...)
```

**为什么不是 heartbeat tick？** 最初 autoDream 和 sessionMemory 放在 heartbeat tick 后触发，但：
1. CC不是靠心跳触发的，是每轮query后（`handleStopHooks`）
2. 心跳30分钟一次太稀疏，可能错过最佳提取窗口
3. 搬到 handle-query 后，每轮对话后都有机会检查，跟CC一致
4. 三个任务都有严格的门控（时间/token/session数），不会每轮都执行

### Session Memory 详细实现

**CC源码结构（`src/services/SessionMemory/`）：**
- `sessionMemory.ts` — 主逻辑
- `sessionMemoryUtils.ts` — 配置/状态管理
- `prompts.ts` — 11 section模板 + 更新prompt
- `index.ts` — 导出

**Engine 搬移（`src/memory/sessionMemory/`）：**
4个文件100%搬移CC源码，适配Engine接口：
- `sessionMemory.ts`（281行）— 用 `QueryEngine` mini agent loop（对齐CC `runForkedAgent`），edit tool更新笔记
- `sessionMemoryUtils.ts`（129行）— 配置阈值+状态追踪
- `prompts.ts`（283行）— CC原版11 section模板
- `index.ts` — 导出

**触发机制（对齐CC）：**
- 上下文 ≥ 10K tokens → 首次初始化（创建 session-notes.md）
- 每增长 5K tokens + 3个 tool calls → 触发更新
- 用 `QueryEngine` + edit/read tool 跑 mini agent loop（同 extract 的模式）

**输出文件：**
- 路径：`{stateDir}/session-memory/session-notes.md`
- 11个 section：Title / Primary Goal / Current State / Key Decisions / Important Context / Files Modified / Errors / User Preferences / Pending / Work Log / Recent Changes
- 用途：compaction 后恢复上下文（`getSessionMemoryForCompaction()`）

**与 extract 的区别：**
| 维度 | extract | sessionMemory |
|------|---------|--------------|
| 目的 | 提取持久化记忆写入 topics/ | 维护当前会话的结构化笔记 |
| 输出 | topics/*.md（长期） | session-notes.md（当前会话） |
| 工具 | read/write/edit/glob/grep | read/edit |
| 生命周期 | 跨session持久 | 单session，compaction后恢复 |

### Auto Dream Gather 阶段的数据源（对齐CC）

CC源码 `consolidationPrompt.ts` 的 Gather 阶段优先级（我们的prompt原文对齐）：

1. **Daily logs**（`memory/daily/YYYY-MM-DD.md`）— 追加式日志，最主要的信号来源
2. **现有记忆文件（topics/）** — 检查是否过时/被证伪
3. **Transcript grep** — **仅按需窄搜索**，明确写了 "Don't exhaustively read transcripts. Look only for things you already suspect matter."

**autoDream 不扫jsonl。** 它读的是 topics 文件和 daily logs，jsonl 只是最后兜底的 `grep -rn "关键词" --include="*.jsonl" | tail -50`，只搜特定词不看全文件。

三个后台任务的数据源对比：

| 任务 | 数据来源 | 是否读jsonl |
|------|---------|------------|
| extract | handle-query直接传 `messages`（内存中的对话） | ❌ |
| sessionMemory | handle-query直接传 `messages`（内存中的对话） | ❌ |
| autoDream | topics文件 + daily logs + 按需grep jsonl | ⚠️ 仅窄搜索兜底 |

### Hook 系统与触发时机

Engine已完整搬移CC的Hook系统（`src/hooks/`），包含所有事件类型：
- `PreToolUse` / `PostToolUse` — tool调用前后
- `PreCompact` / `PostCompact` — compaction前后（**已在autoCompact.ts中使用**）
- `Stop` / `StopFailure` — query loop结束后（**定义了但未注册调用**）
- `SessionStart` / `SessionEnd` — session生命周期

**当前三个后台任务不走Hook注册机制**，而是直接在 `handle-query.ts` 里 fire-and-forget。效果等价于注册在 `Stop` hook上。后续可以正式注册 `executeStopHooks` 把它们包装成callback hook。

### heartbeat.ts 瘦身

搬完后 `heartbeat.ts` 不再包含 autoDream/sessionMemory 逻辑：
- 删掉 `maybeDream()` 方法（45行）
- 删掉 `maybeExtractSessionMemory()` 方法（60行）
- 删掉读 jsonl/解析/估算token 的逻辑
- 心跳现在只负责：tick → 检查离线 → 执行心跳prompt → flush

### 横向对比更新（6/12）

| 维度 | Claude Code | OpenClaw(姐姐) | Engine(小柯) |
|------|------------|----------------|-------------|
| 存储 | 文件系统 | 文件+向量库 | 文件系统 |
| 检索 | LLM sideQuery | 语义搜索(recall) | memory_search语义搜索 |
| 记忆类型 | 4种(user/feedback/project/reference) | 5层(L0-L3) | 4种(对齐CC) |
| Dream整合 | autoDream(24h+5sessions) | 无 | ✅ autoDream(对齐CC) |
| Session笔记 | SessionMemory(11 section) | SESSION-STATE | ✅ SessionMemory(对齐CC) + SESSION-STATE |
| 自动提取 | extract(handleStopHooks) | cron topic-extract | ✅ extract(handle-query fire-and-forget) |
| 触发统一 | handleStopHooks | 分散(cron/心跳) | ✅ handle-query统一 |
| Hook系统 | 完整(20+事件) | 无 | ✅ 完整搬移(定义齐全，部分已使用) |
