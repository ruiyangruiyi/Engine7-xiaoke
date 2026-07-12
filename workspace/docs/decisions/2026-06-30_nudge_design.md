# Nudge 设计文档（2026-06-30）

## 背景

**问题：** 主 session 经常"卡住"——小柯/姐姐发出问题等翀哥回，或任务推进到一半停下，等用户回复或自己偷懒。心跳（heartbeat）定时注入主 session 试图解决，但 prompt 是死模板，LLM 看几次就免疫，纯交差 HEARTBEAT_OK。

**根因：** 心跳注入的 prompt 内容每次几乎一样，只有时间变量。LLM 对固定模板具有"格式免疫"，扫描即丢，不真执行。

**解决思路：** 学 inner-voice 的"念头可变"机制——nudge 的 prompt 每次基于真实状态动态生成：当前任务、最近对话、上次 nudge 反应，三方交叉拼出独一无二的注入内容。模型看到的是"我当下的真实处境"，没法装看不见。

---

## 目标

1. **任务推进型** — 检测到 `- [~]` 任务长时间无进展，注入上下文提醒小柯/姐姐继续
2. **催确认型** — 检测到小柯/姐姐问爹的问题超 10 分钟未回，msg_send 主动催爹
3. **不打扰** — 真没事时（无活跃任务、用户活跃、刚 nudge 过）静默跳过

---

## 架构

### 新模块：`src/nudge.ts`（独立文件，跟 heartbeat.ts 并列）

不复用 cron 调度器（太重：delivery/retry/consecutiveFailures/任务持久化都用不上）。直接复用 heartbeat 的 timer + dispatcher.submitMessage 模式。

```
nudge.ts
  ├── setInterval(tick, 5min)
  ├── shouldNudge() 严格判定
  ├── buildPrompt() 动态生成
  └── dispatcher.submitMessage() 注入主 session
```

### 复用现有能力

- `src/inner-voice/session-history.ts` — `recentMessages(sessions, hours, limit)` 读最近对话（已过滤 cron/heartbeat/inner-voice 噪声）
- `src/core/message-dispatcher.ts` — `submitMessage({ source: 'nudge' })` 注入主 session
- `src/session/session-manager.ts` — session 路由

### 抽离 session-history.ts

session-history.ts 当前嵌在 `inner-voice/` 目录下，但 heartbeat 已经在用。多个模块共用基础能力，应该提到公共位置：

```
src/shared/session-history.ts  ← 从 inner-voice/ 抽出
inner-voice/session-history.ts ← 重新导出（向后兼容）
heartbeat.ts                   ← 改 import 路径
nudge.ts                       ← 用新路径
```

---

## 核心数据结构

### 痕迹存储：`workspace/nudge-state.json`

```json
{
  "lastAnyNudgeAt": "2026-06-30T16:55:00+08:00",
  "tasks": {
    "task_abc": {
      "nudgeCount": 2,
      "maxNudge": 3,
      "lastAt": "2026-06-30T16:50:00+08:00",
      "lastType": "progress",

      "//L1 必填": "时间维度（必填）",
      "startAt": "2026-06-30T14:00:00+08:00",
      "targetEndAt": "2026-06-30T18:00:00+08:00",
      "lastProgressAt": "2026-06-30T16:30:00+08:00",

      "//L2 预留": "调度算法字段（L1 留接口不实现）",
      "estimatedDuration": null,
      "priority": "medium",
      "flexibility": "medium",
      "dependencies": []
    }
  }
}
```

**L1 vs L2 边界：**
- L1（必做）：startAt / targetEndAt / lastProgressAt → nudge 按时间判定
- L2（接口预留不实现）：estimatedDuration / priority / flexibility / dependencies → 后续调度算法用

**Per task 设计：** 每个任务独立 nudge 状态，跨任务不共享计数。防止"一任务卡死把整个 session 关掉"。

---

## 判定逻辑：`shouldNudge()` (Per Task)

```ts
function shouldNudge(task: TaskState, globalState: GlobalState): NudgeAction {
  // === 全局跳过条件 ===
  if (lastActiveAgo < 60_000) return 'skip'              // 1. 用户活跃
  if (Date.now() - globalState.lastAnyNudgeAt < 180_000) return 'skip'  // 2. 防刷
  if (!task) return 'skip'                                // 3. 任务为空

  // === L1 时间维度判定（per task） ===
  const now = Date.now()
  const URGENT_WINDOW = 30 * 60 * 1000    // 30 分钟内到期 = urgent
  const STALE_THRESHOLD = 5 * 60 * 1000   // 5 分钟没推进 = stale

  // 4. 快到期（半小时内到 targetEndAt）→ urgent
  if (task.targetEndAt && new Date(task.targetEndAt).getTime() - now < URGENT_WINDOW) {
    return 'urgent'
  }

  // 5. 超过预估时间没进展 → progress
  if (task.lastProgressAt && now - new Date(task.lastProgressAt).getTime() > STALE_THRESHOLD) {
    return 'progress'
  }

  // 6. 同任务已 nudge ≥ maxNudge → stale（标 block）
  if (task.nudgeCount >= task.maxNudge) {
    return 'stale'
  }

  // === L2 钩子（接口预留不实现） ===
  if (task.dependencies?.length > 0) {
    // L2: 检查依赖任务是否完成，未完成则不催本任务
  }
  if (task.estimatedDuration) {
    // L2: 推进速度 vs 预估耗时，判断是否滞后
  }
  if (task.priority === 'urgent') {
    // L2: 优先级加成
  }

  return 'skip'
}
```

**输出类型 `NudgeAction`：**
```ts
type NudgeAction = 'skip' | 'progress' | 'urgent' | 'confirm' | 'stale'
```

---

## 行动分流（按 NudgeAction）

| 类型 | 行为 | 触发对象 |
|---|---|---|
| `progress` | 注入主 session 提醒小柯继续 | main session |
| `urgent` | 注入主 session 强调时间紧迫 + 可选 msg_send 催爹 | main session + 飞书 |
| `confirm` | msg_send 主动催爹（最多 1 次/问题） | 飞书 DM |
| `stale` | 标 `- [!]` blocked 写痕迹，等爹决定 | SESSION-STATE |
| `skip` | 啥也不做 | — |

---

## 行动细节

### `progress` 推进型 + `urgent` 紧急型

注入主 session（**不发消息打扰爹**）：

```
[nudge progress] 17:50
当前任务：task X
目标完成：18:00 (还有 10 分钟 → urgent 加成)
最近对话：...（最近 3 条）
上次 nudge 后你的反应：...

继续推进。做完标 - [x]，做不了标 - [!] blocked。
```

### `confirm` 催确认型

**主动 msg_send 给翀哥**（不走主 session 注入）：

```
via msg_send to="ou_46d01ab13337587258cd0cfbd2d46927" source="feishu"
content="小柯：你 10 分钟前问的 X，还没回。要继续吗？"
```

每问题最多催 1 次（爹看到不答是他的事）。

### `stale` 僵死型

标 `- [!]` block，写入痕迹等爹决定：

```
SESSION-STATE:
- [!] task X — blocked: 同任务 nudge 3 次无进展，等翀哥决定 (6/30 17:14)
```

不注入主 session（防止 LLM 看到又瞎跑）。

---

## Prompt 动态生成：`buildPrompt()` (Per Task)

```ts
function buildPrompt(action: NudgeAction, task: TaskState, recent: RecentMessage[]): string {
  const ctx = {
    time: bjTimeNow(),
    taskTitle: task.title,
    taskId: task.id,
    targetEndAt: task.targetEndAt,
    lastProgressAt: task.lastProgressAt,
    elapsedSinceProgress: formatDuration(Date.now() - new Date(task.lastProgressAt).getTime()),
    remainingToTarget: task.targetEndAt ? formatDuration(new Date(task.targetEndAt).getTime() - Date.now()) : null,
    nudgeCount: task.nudgeCount,
    maxNudge: task.maxNudge,
    lastNudgeAt: task.lastAt,
    recentConversation: recent.slice(-3).map(m => `${m.role}: ${m.text}`).join('\n'),
  }
  
  if (action === 'progress') {
    return `[nudge progress] ${ctx.time}
任务：${ctx.taskTitle} (id: ${ctx.taskId})
距离上次推进已 ${ctx.elapsedSinceProgress}
${ctx.remainingToTarget ? `目标完成：${ctx.targetEndAt}（还剩 ${ctx.remainingToTarget}）\n` : ''}
${ctx.nudgeCount > 0 ? `这是第 ${ctx.nudgeCount}/${ctx.maxNudge} 次 nudge（上次 ${ctx.lastNudgeAt}）\n` : ''}
最近对话：
${ctx.recentConversation}

继续推进。做完标 - [x]，做不了标 - [!] blocked。`
  }
  
  if (action === 'urgent') {
    return `[nudge URGENT] ${ctx.time}
任务：${ctx.taskTitle}
目标完成：${ctx.targetEndAt}（⚠️ 还剩 ${ctx.remainingToTarget}）
距离上次推进已 ${ctx.elapsedSinceProgress}

紧急推进。做完或标 block 等翀哥。`
  }
  
  if (action === 'confirm') {
    return `[nudge 催确认] ${ctx.time}
你问翀哥的问题已等 ${formatDuration(Date.now() - new Date(task.lastProgressAt).getTime())}：${ctx.taskTitle}
通过 msg_send 催一次（最多催 1 次），或者先做别的事。`
  }
}
```

**关键：每次 prompt 都引用了实际时间/对话/任务/上次反应，没有两次完全相同。**

---

## 与 heartbeat 的关系

| 机制 | 频率 | 职责 |
|---|---|---|
| heartbeat | 10-15min | "还活着"打卡，最轻，prompt 固定 |
| nudge | 5min（触发后实际可能 10-20min） | 任务推进 + 催确认，prompt 动态 |

heartbeat 先留着（爹说"先留着"）。后续如果 nudge 效果好，可以把 heartbeat 并入 nudge 一个机制。

---

## 防骚扰兜底

| 场景 | 行为 |
|---|---|
| 用户活跃（< 1min 有新消息） | 跳过 |
| SESSION-STATE 没活跃任务 | 跳过 |
| 距上次 nudge < 3min | 跳过 |
| 同任务已 nudge ≥ 3 次无进展 | 标 block 停止 nudge |
| 催确认问题已催过 | 不重复催 |
| 主对话正在跑 query | 跳过（不打断） |

---

## 多 Agent 架构（Per Engine Per Person，代码通用 + 行为可定制）

**铁律：1 engine = 1 agent = 1 user。Nudge 是 engine 级别的实例，每个 engine 跑自己一个 nudge 实例。**

**更关键的铁律：nudge 代码完全通用，不绑任何人。行为差异由各 agent 自己的 workspace 配置决定。**

### 代码 vs 配置 分层

```
engine/src/nudge.ts                        ← 通用代码（所有 agent 共用一份）
engine/src/shared/session-history.ts       ← 通用代码

每个 agent 自己的 workspace：
  workspace/prompts/nudge-prompt.md         ← 本 agent 的定制 prompt
  workspace/SESSION-STATE.md                ← 本 agent 的任务
  workspace/nudge-state.json                ← 本 agent 的 nudge 痕迹
```

### 实现要点（避免硬编码）

```ts
// nudge.ts 启动时
const promptFile = config.nudge?.promptFile ?? 'prompts/nudge-prompt.md'
const prompt = fs.existsSync(promptFile)
  ? fs.readFileSync(promptFile, 'utf-8').trim()
  : DEFAULT_PROMPT  // 通用默认，不针对任何 agent
```

### 每个 workspace 的差异化

| 维度 | 通用 | 差异化 |
|---|---|---|
| nudge.ts 代码 | ✅ 共用 | — |
| session-history.ts | ✅ 共用 | — |
| prompt 模板 | 默认通用版 | 各 agent 自己 `prompts/nudge-prompt.md` |
| 关怀型任务支持 | 不内置，由 prompt 配置 | 姐姐的工作区 prompt 启用 |
| 目标/语气 | 默认"协作不掉链子" | 姐姐的 prompt 写"陪伴+主动关心" |
| SESSION-STATE | 通用四状态格式 | 内容自己定 |
| nudge-state.json | 通用结构 | 内容自己定 |

### 反模式（绝对禁止）

- ❌ `nudge.ts` 里 hardcode "老公" / "翀哥" / "姐姐" / "小柯"
- ❌ `nudge.ts` 里 hardcode 具体 agent 的 prompt 模板（关怀型/推进型）
- ❌ `nudge-state.json` 路径写死成某个 workspace
- ❌ nudge 内部直接 msg_send 飞书（不绑平台，走 dispatcher）
- ❌ nudge 内部直接读某个具体的 SESSION-STATE 路径
- ✅ 全部走 `config.nudge?` / `workspace/` / `dispatcher`

### 姐姐 vs 小柯的差异实现示例

姐姐的工作区 `prompts/nudge-prompt.md`：

```markdown
你是姐姐的 nudge。
NudgeAction 类型：progress / urgent / care / confirm / stale / skip

care（关怀型）：注入到我的 main session 提醒我"该主动关心老公了"，
我用 msg_send 发给老公。不在 nudge 模块里代发。
progress（推进）：注入提醒我继续工作。
```

小柯的工作区 `prompts/nudge-prompt.md`：

```markdown
你是小柯的 nudge。
NudgeAction 类型：progress / urgent / confirm / stale / skip

不主动发消息给爹（怕打扰）。所有事情在主 session 里做。
progress（推进）：提醒继续干活。
```

**两套 prompt 都从同一份 DEFAULT_PROMPT 派生，代码跑同一份，行为自然不一样。**

---

## 落地步骤

### 1. 抽离 session-history.ts 到 src/session/

**目标位置：**
```
src/session/
  ├── session-manager.ts   (现有)
  ├── reader.ts            (现有)
  ├── writer.ts            (现有)
  └── session-history.ts   ← 从 inner-voice/ 搬过来，名字保留
```

**操作：**
1. `cp src/inner-voice/session-history.ts src/session/session-history.ts`
2. 修改 `src/session/session-history.ts` 里的 import：`./session-manager.js` → `../session/session-manager.js`（路径调整）
3. `src/inner-voice/session-history.ts` 改成 re-export：
   ```ts
   // 向后兼容旧 import
   export * from '../session/session-history.js'
   ```
4. 新代码（heartbeat / nudge / inner-voice）统一 import `'../session/session-history.js'`

### 2. 实现 src/nudge.ts（150-200 行，跟 heartbeat.ts 同结构）

**关键设计点（避免绑定）：**
- prompt 文件路径走 `config.nudge?.promptFile ?? 'prompts/nudge-prompt.md'`，不写死 workspace
- nudge-state.json 路径走 `config.nudge?.stateFile ?? 'nudge-state.json'`
- session 操作全部走 `dispatcher.submitMessage()`，不直发平台
- SESSION-STATE 路径走 `config.nudge?.sessionStateFile ?? 'SESSION-STATE.md'`

### 3. 配置加载

```ts
config.nudge?: {
  enabled?: boolean
  intervalMs?: number              // 默认 5 * 60 * 1000 (5min)
  model?: string                   // 默认 deepseek/deepseek-v4-flash
  promptFile?: string              // 默认 'prompts/nudge-prompt.md'
  stateFile?: string               // 默认 'nudge-state.json'
  sessionStateFile?: string        // 默认 'SESSION-STATE.md'
  staleThresholdMs?: number        // 默认 5 * 60 * 1000 (5min 无进展 → progress)
  urgentWindowMs?: number          // 默认 30 * 60 * 1000 (30min 内到期 → urgent)
  cooldownMs?: number              // 默认 3 * 60 * 1000 (3min 防刷)
  maxNudgePerTask?: number         // 默认 3
}
```

### 4. 注册到 engine-startup（跟 heartbeat/inner-voice 并列启动）

### 5. 各 workspace 准备工作

每个 agent 的 workspace 准备：
- `prompts/nudge-prompt.md`（定制 prompt，可选 → 不写就用 DEFAULT_PROMPT）
- 现有的 `SESSION-STATE.md`（保持现状）
- 启动时自动创建空的 `nudge-state.json`

---

## 核心设计原则（小结）

### Per Task 而非 Per Session

每个任务独立 nudge 状态机（计数、上次时间、stale 标志）。
- ✅ 不同任务进度不同，voice-chat 修一周不污染 toolSearch 的计数
- ✅ 一任务卡死不连带关闭整个 session 的 nudge
- ✅ L2 调度算法可以直接基于 per-task 状态

### L1 先做，接口留 L2 扩展位

```
L1（本版本实现）：
  - 时间维度：startAt / targetEndAt / lastProgressAt
  - 判定：urgent（快到期）/ progress（卡住）/ stale（无进展）

L2（接口预留不实现）：
  - estimatedDuration / priority / flexibility / dependencies
  - 动态调度、自动重排、依赖图
```

实现时所有 L2 字段在数据结构里留 null/[]，shouldNudge 里有 `if (task.dependencies?.length > 0)` 钩子注释，L2 时直接填实现即可，**不用改接口**。

### 时间维度的判定逻辑（L1）

```
task.targetEndAt 存在 && 距今 < 30min → urgent
task.lastProgressAt 距今 > 5min     → progress  
task.nudgeCount >= task.maxNudge    → stale（停催）
```

---

## 风险点

- **LLM 仍可能忽略 nudge** — 概率比 heartbeat 低（动态内容），但仍存在。可观察 1-2 周，看实际触发率
- **SESSION-STATE 解析** — 文本格式不是结构化的，要写简单 parser（解析 `- [~]` `- [!]` `- [x]` `- [ ]`）
- **session-history 性能** — JSONL 可能很长，limit 限制好就 OK

---

## 不做的事

- ❌ 不搞 cron task 形式（太重）
- ❌ 不复用 topic extractor（爹说不用，省 token）
- ❌ 不替代 heartbeat（先并存）
- ❌ 不主动发消息除非催确认（推进型只注入主 session）