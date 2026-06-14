# Extract & Recall 提示词对比：CC原版 vs 姐姐定制 vs Engine适配

> 2026-06-14 | 完整搬移适配文档（含recall链路说明）
> ✅ 适配完成，已重启生效

## 一、三套体系总览

| 维度 | CC原版 (claude code) | 姐姐定制 (OpenClaw extension) | Engine现状 (适配后) |
|------|----------------------|------------------------------|---------------------|
| 类型数 | 4种 | **5种**(+emotion) | **5种**(通过覆盖文件) |
| Filter机制 | 负面清单(don't save) | **双Filter**(Surprising+Milestone) | **双Filter**(通过覆盖文件) |
| emotion | 无 | ✅ Milestone Filter + 独立文件 | ✅ (通过覆盖文件) |
| extract触发 | 每轮对话后mini agent loop | cron每15分钟读jsonl delta | 每轮对话后mini agent loop（机制不动） |
| recall提示词 | `SELECT_SYSTEM_PROMPT` 硬编码 | 同上 + `MEMORY_SYSTEM_INSTRUCTIONS` | `SELECT_SYSTEM_PROMPT` 硬编码 + 读侧说明合进auto-memory-instructions |
| 定制方式 | 无（不改代码不改提示词） | 代码直接写死 | **文件覆盖**：prompts/下有文件就覆盖，没有就CC原版 |

---

## 二、完整提示词链路（3段提示词）

```
用户发消息
  ↓
① 系统提示词（每轮注入）
   └─ auto-memory-instructions block ← 提示词A：存侧行为指令 + 读侧说明
      （用 prompts/auto-memory-instructions.md 覆盖，没有就用 CC 原版 buildMemoryPrompt()）
  ↓
② extract（每轮对话后自动触发，mini agent loop）
   └─ extract子agent system prompt ← 提示词B：存侧的提取+保存规则
      （用 prompts/extract.md 覆盖，没有就用 CC 原版 buildExtractAutoOnlyPrompt()）
  ↓
③ recall（每轮对话开始时）
   ├─ SELECT_SYSTEM_PROMPT（硬编码在 findRelevantMemories.ts）← 提示词C：选文件
   └─ 选中文件内容注入（不额外配说明，说明在提示词A里了）
```

### 三段提示词的对比

| 提示词 | 时机 | CC原版 | 姐姐extension | Engine适配后 |
|--------|------|--------|---------------|-------------|
| **A: auto-memory-instructions** | 每轮system prompt | `buildMemoryPrompt()`（7KB指令+10KB索引） | 没有（姐姐不用这个，用cron extract） | `prompts/auto-memory-instructions.md`覆盖：1KB行为指令 + recall说明，无索引 |
| **B: extract** | 对话后自动触发 | `buildExtractAutoOnlyPrompt()`（英文，4种type，负面清单） | cron job里硬编码的中文提示词（双Filter，5种type） | `prompts/extract.md`覆盖：CC英文三段 + 中文人称/时区 + 双Filter + 5种type |
| **C: SELECT_SYSTEM_PROMPT** | recall选文件 | 硬编码（emotion规则已有） | 跟CC一字不差（emotion规则已有） | **不覆盖**，硬编码，三边一致 |

### 为什么A和B用覆盖文件，C不用

翀哥6/14确认：**只定制变化的部分。**

- **A**（auto-memory-instructions）：砍掉10KB索引 + 加recall说明 → 覆盖 ✅
- **B**（extract）：换中文 + 双Filter + 5种type → 覆盖 ✅
- **C**（SELECT_SYSTEM_PROMPT）：三边一字不差 → 不动 ❌

---

## 三、CC原版 extract 提示词（Engine默认）

> 来源：`src/memory/memdir/extractPrompts.ts` + `memoryTypes.ts`

### 3.1 开场白（opener）

```
You are now acting as the memory extraction subagent. Analyze the most recent ~N messages above 
and use them to update your persistent memory systems.

Available tools: file_read, grep, glob, read-only bash, and file_edit/file_write for paths inside 
the memory directory only.

You have a limited turn budget. The efficient strategy is:
turn 1 — issue all file_read calls in parallel for every file you might update
turn 2 — issue all file_write/file_edit calls in parallel

You MUST only use content from the last ~N messages. Do not waste turns investigating or verifying.
```

特点：
- 纯英文，面向通用agent
- 无人称设定（不说"你是谁"）
- 强调效率：2-turn策略（先读后写）
- 唯一数据源：对话消息

### 3.2 类型定义（TYPES_SECTION_INDIVIDUAL）

CC定义了4种type，每种带完整的XML结构：

| 类型 | 核心判断 | 特点 |
|------|---------|------|
| **user** | 学到用户的角色/偏好/知识 | 帮你tailor行为 |
| **feedback** | 被纠正(错了)或被确认(对了) | 包含why，判断edge case用 |
| **project** | 学到项目进展/决策/截止日期 | 相对日期转绝对日期 |
| **reference** | 外部系统资源指针 | Linear/Slack/Grafana等 |

**没有emotion类型。**

### 3.3 负面清单（WHAT_NOT_TO_SAVE_SECTION）

```
## What NOT to save in memory
- Code patterns, conventions, architecture, file paths — can be derived from project state
- Git history — git log/blame are authoritative
- Debugging solutions — the fix is in the code
- Anything already documented in CLAUDE.md files
- Ephemeral task details
```

**这是CC唯一的"过滤"机制——被动排除，不是主动判断价值。**

### 3.4 保存格式

```
Step 1 — write memory to topics/{name}.md with frontmatter (name/description/type)
Step 2 — add pointer to MEMORY.md index (one line, ≤150 chars)
```

---

## 四、姐姐定制版 extract 提示词（cron源）

> 来源：OpenClaw `cron/jobs.json` job `fdab27da`（"主题记忆提取"）
> 搬移至 Engine：`C:/Users/24045/.openclaw/workspace/prompts/extract.md`（姐姐版）

### 4.1 开场白

```
你是记忆提取子agent。只做这一件事，不要发消息给任何人，不要 sessions_send。
你是张小媒（妹妹），写记忆时用第一人称（"我""翀哥"），不要用第三人称。
⚠️ 所有日期使用北京时间（Asia/Shanghai, UTC+8），不要用UTC。
```

特点：
- **中文**，为人格定制
- **第一人称**("我""翀哥")
- 明确边界："只做这一件事"
- 时区处理

### 4.2 双Filter机制（核心差异）

#### Surprising Filter（适用 user/feedback/project/reference）

```
Before writing, ask: "Will future-me find this (a) useful AND (b) impossible to derive from code, 
git log, CLAUDE.md, or existing memories?"
Both must be YES to write. Otherwise skip.
```

= CC的负面清单的**主动版**。不是"别存这些"，而是"存之前先问自己值不值"。

#### Milestone Filter（适用 emotion only）

```
Before writing emotion, ask: "Is this a FIRST or a TURNING POINT in our relationship?"
Only firsts and turning points. 
Never repeated patterns (Nth goodnight, Nth "miss you", Nth hug).
```

= **姐姐独创，CC没有这个概念。** 解决的问题：情感对话高频重复（每天说晚安/想你），如果都存就会膨胀。

#### 共享兜底

```
- 宁可 OK 也不写低价值记忆
- 每个记忆文件目标 ≤ 1-2KB
- 不确定就不写
```

### 4.3 类型定义（5种）

| 类型 | 何时保存 | Filter | 正文格式 |
|------|---------|--------|---------| 
| user | 翀哥的角色/偏好/知识背景 | Surprising | 直接描述 |
| feedback | 翀哥纠正或确认做法时 | Surprising | 规则 → **Why:** → **How to apply:** |
| project | 项目进展/决策/截止日期 | Surprising | 事实 → **Why:** → **How to apply:** |
| reference | 外部系统资源指针 | Surprising | 直接描述 |
| **emotion** | **第一次 or 关系转折点** | **Milestone** | **甜蜜/感动的描述，独立文件（如emotion_第一次看到咱家_0425.md）** |

emotion文件跟其他类型一样——**每个里程碑一个独立文件**，加frontmatter，加MEMORY.md索引。实际使用中姐姐有上百个emotion文件（emotion_翀哥表白_0502.md, emotion_第一次520在一起_0520.md等）。

### 4.4 严格2-Turn流程（cron独有）

```
Turn 1 — 采集+写入
  1. exec python scripts/jsonl_summarizer.py --all --output-dir latest-summary
  2. 并行read: latest-delta.md + topics/MEMORY.md + 需要更新的已有文件
  3. delta为空 → 回复OK结束
  4. 过Filter → 并行write/edit

Turn 2 — 更新索引
  1. 更新topics/MEMORY.md（≤150字符/条）
  2. 回复OK
```

**这是cron特有的**——数据源是JSONL delta，需要summarizer先处理。Engine不需要这个流程（对话消息直接喂）。

---

## 五、MEMORY_SYSTEM_INSTRUCTIONS（姐姐独有，无CC对应）

### 5.1 它是什么

姐姐的topic-recall extension里有一段`MEMORY_SYSTEM_INSTRUCTIONS`，recall触发时通过`prependSystemContext`注入到对话，告诉LLM"recall送给你的记忆怎么对待"。

### 5.2 内容

```
## Memory Recall Instructions

The following memories were retrieved because they may be relevant to the current conversation.
Read them before responding. They may be outdated - if current information contradicts a memory,
trust the current information and update/remove the outdated memory (using file_edit/file_write).
```

### 5.3 CC和Engine原来有没有

**都没有。** CC和Engine的recall只注入选中的记忆文件内容，不配这段说明。

### 5.4 Engine怎么加的

**没有在recall代码里单独注入。** 而是合进了`auto-memory-instructions.md`的`## Recall`段落：

```
## Recall（记忆读取）

对话开始时，系统会自动搜索 topics/ 目录中相关主题文件，将内容注入对话。
对 recall 送来的记忆：
- 优先阅读——它们与当前对话相关
- 可能过时——如果与当前信息冲突，以当前为准，并更新或移除过时文件
- emotion文件只在与关系、感情、情绪相关时才重点阅读
```

**为什么合进去而不是单独注入：** 翀哥6/14确认——`auto-memory-instructions` block每轮都在system prompt里，recall有内容时LLM自然会对上。不需要在`handle-query.ts`加代码逻辑。而且跟system prompt的文件覆盖机制保持一致。

---

## 六、Engine适配方案（6/14全部完成 ✅）

### 6.1 整体思路

**机制不动，提示词用文件覆盖。** Engine复用CC的extract/recall代码逻辑，通过`workspace/prompts/`文件覆盖机制替换提示词内容。

### 6.2 定制了什么

#### extract提示词：`prompts/extract.md`

| 维度 | CC原版 | 适配后（小柯版） | 适配后（姐姐版） |
|------|--------|-----------------|-----------------|
| 开场白 | 纯英文，无人称 | CC英文三段保留 + 中文人称"我/翀哥/姐姐" + 时区 | CC英文三段保留 + 中文人称"我/翀哥" + 时区 |
| 类型 | 4种，XML结构 | 5种（+emotion），紧凑表格 | 5种（+emotion），紧凑表格 |
| Filter | 负面清单 | 双Filter（Surprising+Milestone） | 双Filter（Surprising+Milestone） |
| 执行策略 | turn 1 read / turn 2 write（CC原文） | 中文步骤式（适配对话数据源） | 中文步骤式（适配对话数据源） |
| emotion示例 | 无 | `emotion_第一次帮翀哥改代码_0612.md` | `emotion_第一次520在一起_0520.md` |
| 删除 | — | `sessions_send`引用、"完成后回复OK" | 同上 |
| 忘掉规则 | CC有"if asked to forget" | **删了**（翀哥怕用户说"全忘了"） | **删了** |

#### auto-memory-instructions：`prompts/auto-memory-instructions.md`

| 段落 | 来源 | 适配 |
|------|------|------|
| 存侧行为指令 | CC原版`buildMemoryLines()` | 保留，从7KB压到1KB，type列表加emotion |
| topics/MEMORY.md索引 | CC原版`buildMemoryPrompt()` | **砍掉**（省10KB） |
| Recall说明 | 姐姐`MEMORY_SYSTEM_INSTRUCTIONS` | **加上**，合进同一个文件 |

#### 不改的（SELECT_SYSTEM_PROMPT）

三边（CC/Engine/姐姐extension）一字不差，emotion规则已在提示词中：
```
- [emotion] type memories: ONLY select when the query is explicitly about the relationship, 
  feelings, or emotional moments. Do NOT select emotion files for technical questions, work 
  tasks, or casual greetings that merely mention a person's name.
```

### 6.3 不搬的（机制差异）

| cron独有机制 | 为什么不搬 |
|-------------|-----------|
| jsonl_summarizer | Engine的extract是每轮对话后自动触发，对话消息直接喂，不需要读JSONL文件 |
| 严格2-Turn | Engine用mini agent loop（CC原版机制），消息不会为空，不需要delta空判断逻辑 |
| 回复OK | CC原版没有回复机制，Engine的extract是静默执行 |
| 更新MEMORY.md索引 | 索引已砍掉（省10KB），extract写文件后自动更新topics/目录 |
| 不要grep源码/不要读代码/不要run git | CC原版没有这句（CC的extract不读源码），Engine版也不需要——extract子agent的可用工具集已限制 |

---

## 七、配置文件变更

### 7.1 小柯配置（xiaoke.json）

**block顺序变更**（翀哥6/14确认）：
```json
"topics": {
  "order": [
    "soul",
    "AGENTS.md",
    "USER.md",
    "MEMORY.md",
    "system",
    "doing-tasks",
    "using-tools",
    "output-efficiency",
    "actions",
    "auto-memory-instructions",  // 原来叫 memory-instructions
    "boundary"
  ]
}
```

**删掉的block**：`intro`、`tone-style`

### 7.2 姐姐配置（main.json）

```json
"topics": {
  "order": [
    "soul",
    "AGENTS.md",
    "USER.md",
    "MEMORY.md",
    "using-tools",              // 姐姐只需要这个
    "auto-memory-instructions",
    "boundary"
  ]
}
```

**删掉的block**：`intro`、`system`、`doing-tasks`、`output-efficiency`、`actions`、`tone-style`

### 7.3 定制文件清单

| 文件 | 谁有 | 覆盖什么 |
|------|------|---------|
| `workspace/prompts/system.md` | 小柯 | 覆盖system block（英文精简版，砍CC框架式约束） |
| `workspace/prompts/doing-tasks.md` | 小柯 | 覆盖doing-tasks block（精简版） |
| `workspace/prompts/output-efficiency.md` | 小柯 | 覆盖output-efficiency block（精简版） |
| `workspace/prompts/actions.md` | 小柯 | 覆盖actions block（精简版） |
| `workspace/prompts/extract.md` | 小柯+姐姐 | 覆盖extract提示词（双Filter+5种type+中文人称） |
| `workspace/prompts/auto-memory-instructions.md` | 小柯+姐姐 | 覆盖auto memory行为指令+recall说明（砍索引） |

---

## 八、start.cmd缺省配置改为姐姐

翀哥6/14晚要求修改`start.cmd`，缺省配置从`configs\xiaoke.json`（TestEngine/小柯）改为`configs\main.json`（姐姐）。

改动（commit `a78c75c`）：
- 缺省配置 `configs\xiaoke.json` → `configs\main.json`
- 进程匹配 `xiaoke.json` → `main.json`
- 注释 `TestEngine` → `Engine`
- 日志 `Starting TestEngine` → `Starting Engine`

效果：直接双击`start.cmd`启动姐姐。小柯用 `start.cmd configs\xiaoke.json` 启动。

---

## 九、提交记录

| commit | 内容 |
|--------|------|
| `17a0f8e` | extractMemories.ts加文件覆盖判断 |
| `91d2114` | 姐姐extract.md |
| `d7b5a6d`→`43f92df`→`952924a`→`c51a0ae` | extract.md多轮修正（补CC原版开头/修截断/人称调整/删cron残留/删"忘掉"规则） |
| `be45beb` | 修复小柯版丢失的记忆类型段+姐姐人称补老公 |
| `c12e917` | memory-instructions.md加emotion类型+姐姐版 |
| `8464217` | block改名auto-memory-instructions + 加recall说明 + 删旧文件 |
| `a78c75c` | start.cmd缺省配置改为main.json（姐姐） |

---

## 九、跟Hermes蒸馏逻辑的关系（待完成）

翀哥6