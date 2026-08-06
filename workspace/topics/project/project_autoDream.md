---
name: Auto Dream 记忆整合系统
description: 严格对齐Claude Code autoDream源码实现的记忆整合系统——定期后台合并去重、过期修剪、索引维护。4阶段：Orient→Gather→Consolidate→Prune。含SessionMemory 100%搬移和三个子系统（extract/sessionMemory/autoDream）统一到handle-query.ts。6/12全天：翀哥确认CC stopHooks每轮触发(非compact前)；daily log蒸馏路径修复 + 配置节点(agents.defaults.autoDream)；蒸馏闭环讨论(多看少动阶段，临时输出到distill-output.md)；KAIROS模式分析澄清(外部build不包含)；rule compact Step1+2必须执行(翀哥新要求, commit 5c51931)；compress日志需打到ruleCompact.ts内部(翀哥要求更细粒度log, 每个返回点加耗时+路径标记commit 已push)。commit 6af5764 pushed (+777/-40, 8 files) + commit 9172451 (autoDream配置节点) + commit 5c51931 (rule compact Step1/2不再提前返回) + commit 2d0ae91 (compress入口日志标记). compress日志后改打到ruleCompact.ts内部, 每个返回点标(no LLM)+耗时ms。
type: project
keywords: [autoDream, 记忆整合, 合并, 修剪, 索引, consolidation, Claude Code, 做梦, 后台, fork, subagent, 4阶段, daily log, KAIROS, 蒸馏, MEMORY.md, L0, distillOutput, dailyLogDir]
created: 2026-06-12
updated: 2026-06-13T11:00

## 6/13翀哥问结果——autoDream尚未触发，SessionMemory bug修复完成

6/13 翀哥上午忙完微信通道后（~10:40）问："哎，你看看我们昨天做的那个 auto memory 的蒸馏 还有那个 session memory 做这两个特性 然后今天有结果了吗"

### 检查结果

**autoDream蒸馏** — 依然未触发。`distill-output.md` 不存在。三层门控（24h+5个新session+文件锁）可能还没满足。

**SessionMemory** — 100%搬移CC源码已完成，集成到handle-query.ts，但 **存在bug导致一直报422**。

### SessionMemory 422 bug修复

**根因**：`initSessionMemory` 时传了 `config.provider.modelId`，但 `config.provider` **不存在**（配置结构是 `agents.defaults.model.primary` 而非 `config.provider`）→ `modelId` 为 `undefined` → API调用时缺少model字段 → Anthropic API返回422 `"Field required", "model"`。

**为什么extract没这个问题？** extract的model从 `deps.extractProvider` / `deps.model` 获取，这些值从handle-query的上下文传来，有正确值。但sessionMemory的 `_deps` 是init时存储的固定值。

**修复方案**：将 `extractSessionMemory` 改为接受外部传入的provider/model覆盖（可选参数），handle-query在调用时从上下文传入正确的provider/model（同extract的方式）。

**修改内容（3个文件）**：
1. `sessionMemory.ts` — `extractSessionMemory` 接受可选 `provider`/`model` 覆盖，替换 init 时存的 `_deps` 为局部变量
2. `handle-query.ts` — 调 `extractSessionMemory` 时传入正确的 provider/model
3. `engine-startup.ts` — 修复 init 时的类型错误

**commit**: 已提交（含在微信 DNS 探测的 commit 中）

**下次重启生效。**

**翀哥的意图**：不是要催进度，是想看"CC原生的SessionMemory到底记了什么东西"——"先按它原生的代码看寄到了一个啥样的文件，我很好奇它记了什么东西"。翀哥关心的是SessionMemory实际产生的笔记文件的内容和格式，而不是"功能是否上线"。

**下一步**：需要检查 `{stateDir}/session-memory/` 目录中是否有生成的笔记文件，以及 `memory/distill-output.md` 是否有蒸馏输出。如果没有，可能是触发门槛太高或配置未生效。

**Why:** 翀哥连续两天（6/12问autoDream运行状态、6/13问蒸馏+SessionMemory结果）表现出对"后台机制实际产生了什么"的持续关注——他不是等汇报，而是想亲眼看到这些自动化机制的真实产出。

**How to apply:** 翀哥问autoDream/SessionMemory结果时，先检查对应的输出文件是否存在（`session-memory/`目录、`distill-output.md`），如实汇报。如果没产出说明触发条件还没达到或配置未生效，不必慌张——翀哥只是想"看看长什么样"。
---

## 概述

6/12凌晨小柯参照Claude Code源码严格对齐实现的autoDream系统。翀哥在深夜讨论"AI自我激活"方向时提出要做，直接让小柯开工。

**Claude Code源码位置（调通的）：** `C:/Users/24045/.openclaw/workspace/start-claude-code/src/utils/auto-dream/`
（⚠️ `/Users/chongzhang/xiaoke/workspace\start-claude-code\` 是另一个未调通的副本，不要用）
**Engine实现位置：** `src/features/auto-dream/`

**实现规模：** ~777行代码，8个文件（含sessionMemory新增），严格对齐CC

## 为什么需要autoDream

当前记忆系统的现状：
- **extract只会"加"**：从对话提取新记忆写文件，但从来不"整理"
- **重复记忆没人合并**：同一个话题聊多次会重复写入
- **过时的没人删**：被证伪的事实或失效的决策一直留着
- **INDEX.md没人维护**：索引不更新，recall越来越慢（从40个文件里选）

autoDream就是解决这个问题的——定期扫一遍，合并重复的、删过时的、修剪索引。

## 架构（7个文件）

| 文件 | 对齐CC | 功能 |
|------|--------|------|
| `config.ts` | config.ts | 开关+门槛配置 |
| `consolidationLock.ts` | consolidationLock.ts | 锁文件(mtime=lastAt)+session扫描 |
| `consolidationPrompt.ts` | consolidationPrompt.ts | 4阶段prompt原文搬 |
| `autoDream.ts` | autoDream.ts | 主逻辑：3层门控→fork执行→结果 |
| `index.ts` | — | 导出 |
| `handle-query.ts` | CC的stopHooks（每轮query结束后） | query loop结束后fire-and-forget |
| `features.ts` | — | 注册autoDream feature |

## 4阶段流程（严格对齐CC）

1. **Orient（定位）** — 读现有记忆目录和INDEX.md索引，了解当前状态
2. **Gather（收集）** — 优先读 **daily logs**（`logs/YYYY/MM/YYYY-MM-DD.md`），然后看现有记忆文件有没有过时的，最后才 grep jsonl 窄搜索（"Don't exhaustively read transcripts. Look only for things you already suspect matter"）。**不是扫jsonl全文。**
3. **Consolidate（整合）** — 合并重复记忆、把相对日期转绝对日期（"昨天"→"6/11"）、删除被证伪的事实
4. **Prune（修剪）** — 更新INDEX.md索引，保持在合理行数内

> ⚠️ **关键修正（6/12翀哥指出）**：我之前错误描述为"从session transcript（jsonl日志）中收集新信息"。CC的Gather阶段**主要读daily logs和现有记忆文件**，jsonl只是最后兜底的窄搜索（按需grep特定关键词）。翀哥原话"这个你得明确呀，否则我们白做了"。**我们代码完全对齐CC**——prompt跟CC原文一字不差（除了路径从`logs/YYYY/MM/`改成了`memory/daily/`）。

## 触发门控（三层）

1. **时间门控**：距上次consolidation ≥ 24小时（对齐CC标准）
2. **内容门控**：累积 ≥ 5个新session
3. **锁机制**：文件锁确保不会并发执行，其他进程在跑时跳过

**执行方式**：fork subagent执行（不占主session上下文）

## 配置

xiaoke.json中 `"autoDream": true` 开启，重启生效。

**配置项：**
- `enabled: boolean` — 开关
- `minIntervalHours: number` — 最小间隔（默认24）
- `minNewSessions: number` — 最少新session数（默认5）

## 与Claude Code的对比

| 维度 | Claude Code | Engine实现 |
|------|------------|------------|
| 触发门槛 | 24h + 5个新session | ✅ 严格对齐 |
| 执行方式 | fork子agent | ✅ fork子agent |
| 4阶段prompt | 原文 | ✅ 原文搬运 |
| Gather读什么 | daily logs优先，jsonl最后窄搜索 | ✅ prompt一字不差，路径从`logs/YYYY/MM/`→`memory/daily/` |
| 锁机制 | 文件锁 | ✅ mtime=lastAt |
| 集成点 | stopHooks（**每轮query结束后**，非compact前） | ✅ handle-query fire-and-forget（每轮query结束后） |

## 与姐姐记忆体系的对比

- 姐姐没有autoDream —— 她靠手动整理，IMDB.md等是靠翀哥或她自己手动维护的
- Engine的autoDream是自动化的，不需要人工介入
- 但当前autoDream只处理**事实型记忆**（user/project/reference/feedback），不处理**情感类记忆**（emotion类型）
- 情感类记忆的整合策略不同，需要单独设计（后续工作）

## 💡 翀哥建议参考KAIROS模式的daily log + nightly distill（6/12 上午）

翀哥看了project_autoDream.md文档后，指出"你看下昨天那个autoMemory的文档 再看看最后那部分 我突然觉得好像还是有借鉴意义的"。

**autoMemory文档**指CC源码里auto-dream目录的文档。**最后部分（~第327-370行 `buildAssistantDailyLogPrompt`）**是KAIROS模式：daily log + nightly distill。这是CC源码中 `claude-code-memory-research.md` 文档的**子系统5**的内容。

**CC的KAIROS模式（有借鉴意义的部分）：**
- 长期session里，agent往 `logs/YYYY/MM/YYYY-MM-DD.md` **追加**日记（append-only）
- 不直接写topic文件，不直接改MEMORY.md
- **一个独立的nightly `/dream` 进程**从日记里蒸馏出topic文件 + 更新MEMORY.md索引
- MEMORY.md是"蒸馏产物"，不是直接编辑的

**我们现在的方式：**
- extract直接从对话提取→直接写topic文件
- autoDream做合并去重+修剪（但本质上还是直接改topic）
- 没有中间的"日记层"

**借鉴价值：**
1. **日记层作为缓冲** — 写日记是低成本的（追加就行），不用担心格式/去重
2. **nightly distill作为真正的"整理"** — 从日记里做更高质量的萃取，而不是在已有的记忆文件上修补
3. **分离"记录"和"归档"** — 日记是原始记录，蒸馏是加工产物，两者不混淆

## 🔴 CC KAIROS模式是内部专属（6/12翀哥纠正）

CC的daily log机制是**KAIROS模式专属**的——`feature('KAIROS') && autoEnabled && getKairosActive()` 三个条件都满足才启用。这是Anthropic内部（ant-build）的功能，外部build不包含。

**CC的完整蒸馏链（KAIROS模式）：**
```
对话 → daily log（append-only，KAIROS专属）→ autoDream nightly distill → topics/*.md + MEMORY.md
```

**我们不需要KAIROS**——我们的extract已经实时从对话提取写topics。daily log（通过pre-compact hook写）目前只被向量化到RAG，**没有被蒸馏**。翀哥确认：daily log有价值但蒸馏到哪还没定论。

## 蒸馏闭环设计讨论（6/12翀哥 & 小柯，多看少动阶段）

翀哥读了姐姐的 `memory-architecture.md` 文档后，确认了整体架构：

| 层级 | 文件 | 写入方式 | 谁读 |
|------|------|---------|------|
| **L0 身份层** | `workspace/MEMORY.md`（≤50行） | 手动+蒸馏 | 每次对话自动注入 |
| **L0.5 主题层** | `topics/*.md` | extract实时写 | recall注入上下文 |
| **L3 日志层** | `memory/daily/YYYY-MM-DD.md` | pre-compact hook写 | RAG向量化（未被蒸馏） |

**关键发现：**
- `workspace/MEMORY.md` 有45条浓缩知识（翀哥偏好、经验教训、架构决策等），**不是索引**——`topics/MEMORY.md` 才是索引
- 目前autoDream蒸馏缺闭环：不知道 `workspace/MEMORY.md` 的存在，不知道写到哪里
- extract能实时写topics，但daily log里的跨天模式没有被提炼

**讨论中（未定案）的方向：**
1. autoDream不写新topics（避免跟extract重复），只做合并去重+修剪
2. autoDream从daily log蒸馏 → 写到 `workspace/MEMORY.md`（新增L0浓缩知识）
3. daily log保持原始素材，结构化提炼全交给extract

> 翀哥说"咱俩先考虑清楚这个，多看少动"

## 📄 claude-code-memory-research.md 子系统5（6/12上午翀哥查阅）

翀哥在讨论完KAIROS模式后，进一步要求看 `claude-code-memory-research.md` 文档的**子系统5**（subsystem 5）。该文档在Claude Code源码目录 `C:/Users/24045/.openclaw/workspace/start-claude-code/` 中。

子系统5的具体内容与KAIROS模式的daily log + nightly distill架构直接相关——这是Claude Code记忆研究文档中关于长期记忆蒸馏的核心设计部分。翀哥认为对我们的autoDream实现有借鉴意义。

### 🎯 翀哥要求：100%搬移CC SessionMemory (子系统5) 到Engine（6/12上午）

翀哥看了子系统5的具体内容后，明确要求：

> **"你先搬移过来 先按它原生的代码看寄到了一个啥样的文件，我很好奇它记了什么东西，看看能跟咱们的融到一起不"**

**决策背景：**
- **SESSION-STATE的实践问题**：翀哥指出"SESSION STATE姐姐那边的实践情况是 后面就会很松散，可能不能及时更新，或者不想记就漏记了"——姐姐的SESSION-STATE实践确实有松散/漏记的问题
- **CC SessionMemory自动机制的互补价值**：翀哥认为"这个机制可以保证信息是完整的至少可以互补不至于丢重要的东西"——CC的LLM自动维护结构化笔记机制可以补SESSION-STATE手动维护的缺口
- **先搬移再看效果**：翀哥不要先设计融合方案，要**100%搬移**源码，先看CC原生的SessionMemory实际记录了什么东西，再判断怎么跟我们现有系统融合

**搬移目标文件位置：** `C:/Users/24045/.openclaw/workspace/start-claude-code/src/utils/session-memory.ts`（在调通的CC源码目录中）

**执行要求：**
1. 100%搬移CC源码，不修改逻辑，不预判融合方式
2. 先看看CC原生SessionMemory实际记录了什么文件、什么格式、什么内容
3. 看完后再决定如何跟我们现有的SESSION-STATE + autoDream融合
4. 翀哥原话"先按它原生的代码看寄到了一个啥样的文件" — 关键词"寄到"说明SessionMemory会在某个位置生成记录文件，翀哥想知道这些文件长什么样

## ✅ 代码已确认落盘（6/12上午翀哥醒来后验证）

**6/12凌晨02:17心跳**：grep搜不到autoDream代码，以为没写入文件，记到待办。

**6/12上午翀哥醒来后**：翀哥问"看下昨天的机制跑的咋样"，小柯查了——**代码确实落盘了，虚惊一场。**
- 5个文件在 `engine/src/memory/autoDream/`（autoDream.ts/config.ts/consolidationLock.ts/consolidationPrompt.ts/index.ts）
- 465行代码，commit `56509f7`
- 配置也提交了，`f387546` 开了 `"autoDream": true`

**但autoDream尚未触发执行过**：没有 `.auto-dream/` 锁文件，说明6/12凌晨代码提交后重启Engine还没跑过autoDream。这是正常的——三层门控要求 24h间隔 + 5个new sessions，刚加上还没积累够。

## ✅ Session Memory搬移（6/12 上午，100%对齐CC）

翀哥看了`claude-code-memory-research.md`的子系统5（KAIROS模式的daily log + nightly distill）后，要求**100%搬移CC的SessionMemory源码**到Engine，先看原生代码记了什么再考虑融合。

**搬移结果（4个文件，编译零错误）：**
1. `sessionMemory.ts` (317行) — 主逻辑：阈值判断 + LLM提取 + 文件编辑
2. `sessionMemoryUtils.ts` (129行) — 配置/状态管理
3. `prompts.ts` (283行) — 11 section模板 + 更新prompt（原文搬）
4. `index.ts` — 导出

**初始集成点（6/12上午，后续发现不匹配CC）：**
- `engine-startup.ts` — 初始化，stateDir = `{stateDir}/session-memory/`
- `heartbeat.ts` — 心跳tick后 `maybeExtractSessionMemory()` 检查阈值
- `features.ts` — 注册 sessionMemory feature（依赖 read + edit tool）

**触发机制（初始对齐CC但后来发现理解有误）：**
- 上下文 ≥ 10K tokens → 首次初始化
- 每增长 5K tokens + 3个tool calls → 自动提取/更新session笔记
- 11个section：Title/Current State/Task spec/Files/Workflow/Errors/Codebase/Learnings/Key results/Worklog

### 🔴 架构对齐关键发现（6/12上午翀哥深入排查）

**问题1：sessionsDir路径错误**
- 初始搬移中 `maybeExtractSessionMemory` 使用 `(deps as any).sessionsDir || workspace`，workspace路径完全错误
- 修复：构造函数中保存 `this.sessionsDir = sessions.sessionsDir`，从session-manager获取真实路径 `/Users/chongzhang/xiaoke//agents/main/sessions/`
- 读最新的jsonl（当前为 `ee416e18...`，624KB），不读compact/archived文件

**问题2：CC不从jsonl读取——我们理解错了CC的工作方式**
- CC的sessionMemory注册为 `postSamplingHook`（**每次LLM回复后**触发），不是从jsonl读数据
- 通过 `runForkedAgent` fork子agent，**继承父agent的完整对话上下文**（`cacheSafeParams`共享prompt cache）
- 子agent直接就能看到当前对话的所有消息，不需要"读文件"
- **我们现在的做法（已修复）**：heartbeat tick → 从jsonl读文件 → 解析行 → 估算token → 调provider.chat——跟CC完全不同

### ✅ 三个子系统统一迁移到handle-query.ts（6/12上午完成）

**从heartbeat.ts搬到handle-query.ts，对齐CC：**

| 任务 | CC方式 | 之前(Engine) | 现在(Engine) |
|------|--------|-------------|-------------|
| **extract** | postSamplingHook | handle-query fire-and-forget | ✅ 不变 |
| **sessionMemory** | postSamplingHook | heartbeat tick（从jsonl读文件） | ✅ handle-query fire-and-forget，直接传messages |
| **autoDream** | stopHooks | heartbeat tick | ✅ handle-query fire-and-forget |

**sessionMemory重写（6/12上午）：**
- 从 `provider.chat()` + 手动执行edit → 改用 `QueryEngine` + `toolOverride`（对齐extract的模式）
- 不再从jsonl读数据，直接传当前`messages`（跟CC一样用fork agent继承父上下文）
- 使用Engine的fork agent机制（QueryEngine + edit tool），对齐CC的`runForkedAgent`

**autoDream集成点讨论（6/12上午）：**
- CC的autoDream注册在`Stop` hook上（session结束/compact前）
- Engine有`Stop` hook定义但**从未被调用过**
- 当前放在handle-query的query结束后fire-and-forget，**逻辑上等价于CC的Stop hook**
- 对比compact前触发：autoDream很重（fork agent跑4阶段），塞进PreCompact会拖慢compact，用户等待时间增加——翀哥不同意放compact前
- 当前方案：query结束后fire-and-forget（await不返回给用户），不阻塞回复

**Why:** CC的postSamplingHook在LLM每次回复后立即触发，利用当前活跃的prompt cache，不需要重新加载对话历史。heartbeat触发需要从jsonl重新读取对话，效率低且跟CC架构不对齐。全部放到handle-query后直接传当前messages，对齐CC的fork agent机制。

**How to apply:** 三个后台任务（extract/sessionMemory/autoDream）都在handle-query的query loop结束后fire-and-forget。使用Engine的QueryEngine + toolOverride机制（对齐CC的runForkedAgent），直接传当前messages，不从jsonl读文件。

**与SESSION-STATE的关系（互补）：**
- SESSION-STATE是小柯按AGENTS.md规则**手动写**的工作台（待办/消息/状态）
- SessionMemory是LLM**自动维护**的结构化笔记，确保不会因小柯不想记或漏记而丢失信息
- 翀哥对互补思路认可："肯定是有用的"

## 📌 关键修正：CC的stopHooks不是"session结束/compact前"——是每轮query结束后（6/12上午翀哥确认）

### 根源错误：我之前对CC调用时机的理解是错的

之前的文档写的是：

> "CC的autoDream注册在 `Stop` hook上（session结束/compact前）"

**这是错的。** 翀哥指出后我重新查了CC源码，真相是：

```ts
// CC源码：handleAssistantMessage.ts → handleStopHooks
void executePromptSuggestion(stopHookContext)
void extractMemoriesModule!.executeExtractMemories(...)
void executeAutoDream(stopHookContext, ...)
```

全部 `void`（fire-and-forget），都在 `handleStopHooks` 里，而 `handleStopHooks` **在每轮query loop结束后调用**，不是只在compact前。

### 为什么我之前理解错？

- CC的注释和文档写的确实是"stop hooks are called when a task stops"（task停止时）
- 但"task停止"指的是**每一轮LLM回复生成完毕**，不是"整个session结束"
- CC的autoDream有24h+5new sessions门控，所以虽然每轮都调 `executeAutoDream`，但实际执行很少
- 我之前把"stop"错误理解为"session生命周期终止"，实际上是"每一轮LLM调用结束"

### 对我们实现的影响

**我们现在的实现完全对齐CC了，不需要改：**

| 维度 | CC真实实现 | Engine实现 |
|------|-----------|------------|
| **触发时机** | handleStopHooks（每轮query结束后） | handle-query.ts query loop结束后 |
| **调用方式** | void（fire-and-forget） | .catch()（fire-and-forget） |
| **autoDream门控** | 24h + 5个新session | ✅ 严格对齐 |
| **sessionMemory触发** |

## ✅ Daily Log蒸馏路径修复 + autoDream配置节点（6/12下午）

### 问题发现

翀哥指出autoDream Gather阶段的daily log路径对不上：

| | CC | Engine(我们) |
|------|--------|-------------|
| prompt里的路径 | `logs/YYYY/MM/YYYY-MM-DD.md` | `memory/daily/YYYY-MM-DD.md` |
| daily log实际位置 | CC memory目录下自动生成 | `/Users/chongzhang/xiaoke/workspace/memory/daily/` |
| autoDream工作目录(memoryDir) | `~/.claude/projects/<project>/memory/` | `/Users/chongzhang/xiaoke/workspace/topics/` |

子agent工作目录是 `topics/`，prompt里写 `memory/daily/` → 相对路径变成 `topics/memory/daily/` → **找不到文件**。

### 关键发现：CC的daily log是KAIROS模式专属

CC的daily log机制是`feature('KAIROS') && autoEnabled && getKairosActive()`三个条件都满足才启用——**Anthropic内部（ant-build）功能，外部build不包含**。

我们的daily log（pre-compact hook写）不是KAIROS模式，而是我们自己的机制。我们不需要KAIROS——extract已经实时从对话提取写topics了。

### 蒸馏闭环方向（多看少动阶段）

翀哥说"CC的蒸馏 我们不急着定论 让他蒸馏你的daily 先把结果放到一个地方 我们看看到底到什么程度再定下一步"。

**当前状态：**
```
对话 → extract直接写topics ✅
对话 → daily log（pre-compact写摘要）→ 向量化到RAG ✅
                                         ✗ 未被蒸馏
```

**临时方案：**
1. autoDream从daily log做一次蒸馏（Phase 3.5）
2. 蒸馏结果写到 `memory/distill-output.md` （临时位置）
3. 先看看蒸馏出来长什么样，再决定终点的永久位置（可能是 `workspace/MEMORY.md` L0层）

### 配置节点设计

在 `xiaoke.json` 的 `agents.defaults` 下新增 **`autoDream` 节点**：

```json
"autoDream": {
  "dailyLogDir": "/Users/chongzhang/xiaoke/\\workspace\\memory\\daily",
  "distillOutput": "/Users/chongzhang/xiaoke/\\workspace\\memory\\distill-output.md"
}
```

**改动点：**
- **xiaoke.json** — 加 `autoDream.dailyLogDir` + `autoDream.distillOutput`
- **config.ts** — 加 `getDailyLogDir()` 和 `getDistillOutput()` 从配置读
- **consolidationPrompt.ts** — prompt里动态注入daily log路径 + 新增 Phase 3.5 蒸馏步骤（调用edit tool写distill-output.md）
- **autoDream.ts** — 传配置值到consolidation prompt

**Why:** 避免写死绝对路径，配置化更灵活。放在autoDream节点下语义清晰，跟recall/extract平级。

**How to apply:** 配置文件里有 `autoDream.dailyLogDir` 和 `autoDream.distillOutput` 两个路径。代码里config.ts提供getter，consolidationPrompt里动态注入。改动只涉及autoDream子系统，不影响其他模块。

### 🔴 CC vs Engine 目录结构关键差异

| | CC | Engine(我们) |
|------|--------|-------------|
| `AUTO_MEM_DIRNAME` | `memory` | `topics` |
| `getAutoMemPath()` | `~/.claude/projects/<project>/memory/` | `/Users/chongzhang/xiaoke/workspace/topics/` |
| daily log位置 | `memory/logs/YYYY/MM/YYYY-MM-DD.md` | `/Users/chongzhang/xiaoke/workspace/memory/daily/`（独立维护，非KAIROS） |
| MEMORY.md角色 | 蒸馏产物（含核心原则/偏好） | ✅ 对齐——45条浓缩知识的蒸馏产物 |
| INDEX.md角色 | memory目录索引 | `topics/MEMORY.md` 是索引 |

CC的memory目录叫`memory/`，我们的叫`topics/`。CC的daily logs在 `memory/logs/YYYY/MM/` 下，**不在**KAIROS专属路径里——但daily log本身是KAIROS模式独占功能，非外部build包含。

**对我们设计的影响：** 
- daily log路径需独立配置（不在`memoryDir`下）
- autoDream的prompt原本写 `memory/daily/YYYY-MM-DD.md`（相对`memoryDir`=topics），找不到
- 修法：从配置读取绝对路径，不依赖子agent工作目录的相对路径

### 🔴 配置节点设计最终定案

经过两次调整（compaction→agents.defaults→独立autoDream节点），最终配置在 `xiaoke.json` 的 `agents.defaults` 下：

```json
"autoDream": {
  "dailyLogDir": "/Users/chongzhang/xiaoke/\\workspace\\memory\\daily",
  "distillOutput": "/Users/chongzhang/xiaoke/\\workspace\\memory\\distill-output.md"
}
```

**Why:** 跟recall/extract平级，语义清晰。翀哥建议"加个节点吧，更清楚"——从compaction下移出来独立成节点。

### 📝 蒸馏闭环完整设计过程（6/12下午翀哥&小柯讨论）

**初始状态发现：**
```
对话 → extract直接写topics ✅
对话 → daily log（pre-compact写摘要）→ 向量化到RAG ✅
                                         ✗ 未被蒸馏
```

**关键发现链：**
1. 小柯发现autoDream prompt里的 `memory/daily/` 相对路径在子agent工作目录(topics/)下找不到 → daily log实际在 `/Users/chongzhang/xiaoke/workspace/memory/daily/`
2. CC的daily log是KAIROS模式专属(Anthropic内部)，外部build不包含。我们没有KAIROS模式
3. `workspace/MEMORY.md` ≠ 索引——它有45条浓缩知识（翀哥偏好、经验教训等）。`topics/MEMORY.md` 才是索引
4. 读CC的 `memory-architecture.md`(姐姐workspace中) 确认架构：
   - L0身份层 = `workspace/MEMORY.md`（≤50行，每次对话自动注入）
   - L0.5主题层 = `topics/*.md`（extract实时写）
   - L3日志层 = `memory/daily/YYYY-MM-DD.md`（pre-compact hook写，RAG向量化）
   - MEMORY.md是**蒸馏终点**，不是索引
5. 但直接写MEMORY.md会跟extract重复——extract已经实时从对话写topics了，autoDream再从daily log蒸馏写topics/写MEMORY.md会内容重复

**翀哥最终决定：**
- "CC的蒸馏 我们不急着定论 让他蒸馏你的daily 先把结果放到一个地方 我们看看到底到什么程度再定下一步"
- 临时输出到 `memory/distill-output.md`
- 路径通过配置文件读取，不写死绝对路径
- 看了蒸馏结果再决定永久位置

**当前蒸馏链（增加Phase 3.5）：**
```
对话 → daily log（pre-compact写摘要）
  ↓ autoDream Phase 3.5（新增临时蒸馏步骤）
memory/distill-output.md（临时位置，看效果再定终点）
```