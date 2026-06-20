# Claude Code Task 系统深度分析

> 调研时间：2026-06-20 02:53  
> 源码路径：`C:/Users/24045/.openclaw/workspace/start-claude-code/`

## 核心发现：两套独立的 Task 系统

Claude Code 里有**两套完全独立的 task 管理系统**，用途不同，存储不同，状态机也不同。

| 系统 | 用途 | 存储 | 状态 | 持久化 |
|------|------|------|------|--------|
| **V1 TodoWrite** | 简单待办清单 | 内存 `AppState.todos` | pending/in_progress/completed | ❌ compaction 丢失 |
| **V2 Task** | 项目级任务管理 + 团队协作 | 磁盘 JSON 文件 | pending/in_progress/completed/deleted | ✅ 重启保留 |

另外还有一套 **Runtime Task** 用于管理后台进程（shell 命令、子 agent、dream 等），但那是执行层面的，不是项目管理的。

---

## V1 TodoWrite：轻量级内存待办

### 数据模型

```typescript
// src/utils/todo/types.ts
TodoItem = {
  content: string      // 待办内容
  status: 'pending' | 'in_progress' | 'completed'
  activeForm: string   // 进行时描述（用于 spinner）
}

TodoList = TodoItem[]  // 就是个数组
```

### 存储方式

- 存在 `AppState.todos[agentId]` 里（React state）
- 每个 agent 有自己的 todo list（按 agentId 或 sessionId 隔离）
- **纯内存**，compaction 或重启就没了

### 状态转换

```
pending → in_progress → completed
```

就这么简单，没有任何守卫、依赖、通知机制。LLM 调 TodoWrite 工具直接覆盖整个列表。

### 我们 Engine7 的现状

我们搬了 V1（`TodoWriteTool`），行为完全一致。但也继承了它的缺点：**compaction 就丢**。

---

## V2 Task：项目级任务管理 + 团队协作 ⭐

这是重点。Claude Code 的 V2 Task 系统是为**多 agent 团队协作**设计的，有完整的状态机、持久化、并发控制、通知机制。

### 数据模型

```typescript
// src/utils/tasks.ts
Task = {
  id: string              // 自增数字（"1", "2", "3"...）
  subject: string         // 简短标题
  description: string     // 详细描述
  activeForm?: string     // spinner 文字
  owner?: string          // 负责人（agent ID 或名字）
  status: 'pending' | 'in_progress' | 'completed'
  blocks: string[]        // 此任务阻塞哪些任务
  blockedBy: string[]     // 此任务被哪些任务阻塞
  metadata?: Record<string, unknown>  // 任意扩展字段
}

// TaskUpdateTool 额外支持伪状态 'deleted'（触发文件删除）
```

### 存储方式

每个 task 是一个独立的 JSON 文件：

```
~/.claude/tasks/{taskListId}/{taskId}.json
```

比如：
```
~/.claude/tasks/my-team/1.json
~/.claude/tasks/my-team/2.json
~/.claude/tasks/my-team/3.json
```

还有一个 `.highwatermark` 文件记录历史最大 ID，防止删除后 ID 复用。

### 状态机（完整版）

```
                    TaskCreate
                        │
                        ▼
                   ┌─────────┐
                   │ pending │◄────────────────────┐
                   └────┬────┘                     │
                        │                          │
            TaskUpdate(status='in_progress')       │
            [自动设 owner（swarm 模式）]            │
                        │                          │
                        ▼                          │
                 ┌─────────────┐                   │
                 │ in_progress │                   │
                 └──────┬──────┘                   │
                        │                          │
        TaskUpdate(status='completed')             │
        [先跑 TaskCompleted hooks]                 │
        [hook 可以阻止完成]                         │
                        │                          │
                        ▼                          │
                  ┌───────────┐                    │
                  │ completed │                    │
                  └───────────┘                    │
                                                   │
        ┌──────────────────────────────────────────┘
        │
        │  teammate 死亡/退出
        │  unassignTeammateTasks()
        │  → owner 清空, status 重置为 pending
        │
        └──────────────────────────────────────────►
```

### 关键转换规则

#### 1. pending → in_progress（自动 owner）

```typescript
// TaskUpdateTool.ts:188-199
if (status === 'in_progress' && !task.owner && isAgentSwarmsEnabled()) {
  task.owner = currentAgentName  // 自动认领
}
```

**意义**：防止两个 agent 同时做一个任务。谁先开始，谁就是 owner。

#### 2. in_progress → completed（Hook 守卫）

```typescript
// TaskUpdateTool.ts:232-265
const hookResults = await executeTaskCompletedHooks(task)
if (hookResults.some(r => r.blockingError)) {
  return { success: false, error: 'Hook blocked completion' }
  // 任务保持 in_progress，不会变成 completed
}
```

**意义**：外部可以阻止任务完成。比如跑个测试 hook，测试没过就不让完成。

#### 3. 任意 → deleted（伪状态，触发删除）

```typescript
// TaskUpdateTool.ts:214-220
if (status === 'deleted') {
  await deleteTask(taskListId, taskId)
  // 更新 .highwatermark
  // 从其他任务的 blocks/blockedBy 里移除此 ID
  // 删除 JSON 文件
}
```

#### 4. TaskCreate（Hook 守卫 + 回滚）

```typescript
// TaskCreateTool.ts:80-129
const task = await createTask(...)  // 写 JSON 文件
const hookResults = await executeTaskCreatedHooks(task)
if (hookResults.some(r => r.blockingError)) {
  await deleteTask(taskListId, task.id)  // 回滚
  throw new Error('Hook blocked creation')
}
```

### 并发控制：两层锁

```typescript
// src/utils/tasks.ts
const LOCK_OPTIONS = {
  retries: 30,
  minTimeout: 5,
  maxTimeout: 100,
}
// 总预算约 2.6 秒，支持 10+ 并发 agent
```

| 操作 | 锁级别 | 原因 |
|------|--------|------|
| 普通 CRUD | 单任务文件锁 `{id}.json` | 粒度细，并发高 |
| claimTask + busy-check | 列表级锁 `.lock` | 需要原子读所有任务检查 busy |

### Claim 机制（认领任务）

```typescript
// src/utils/tasks.ts:541-612
async function claimTask(taskListId, taskId, claimantAgentId, options) {
  // 1. 加锁
  // 2. 检查：
  //    - task_not_found: 任务不存在
  //    - already_claimed: 已被其他 agent 认领
  //    - already_resolved: 已完成
  //    - blocked: 被未完成的前置任务阻塞
  //    - agent_busy: (busy-check 模式) 认领者已有未完成的任务
  // 3. 设 owner = claimantAgentId
  // 4. 解锁
}
```

**注意**：LLM 不直接调 `claimTask()`，而是通过 `TaskUpdateTool` 设 `owner` 字段。`claimTask` 是给 SDK/外部编排器的 API。

### 依赖管理（blocks / blockedBy）

```typescript
// TaskUpdateTool 支持两个字段：
addBlocks: string[]     // 此任务完成后，哪些任务可以开始
addBlockedBy: string[]  // 此任务要等哪些任务完成

// 内部实现：
function blockTask(listId, fromTaskId, toTaskId) {
  // fromTask.blocks.push(toTaskId)
  // toTask.blockedBy.push(fromTaskId)
}
```

**查询时自动过滤**：
```typescript
// TaskListTool.ts:72-83
const completedIds = tasks.filter(t => t.status === 'completed').map(t => t.id)
tasks.forEach(t => {
  t.blockedBy = t.blockedBy.filter(id => !completedIds.includes(id))
})
// LLM 只看到未完成的阻塞项
```

### 多 Agent 共享：getTaskListId()

```typescript
// src/utils/tasks.ts:199-210
function getTaskListId(): string {
  // 优先级：
  // 1. CLAUDE_CODE_TASK_LIST_ID 环境变量（显式覆盖）
  // 2. In-process teammate context（用 leader 的 team name）
  // 3. CLAUDE_CODE_TEAM_NAME 环境变量（tmux/iTerm2 进程 teammate）
  // 4. leaderTeamName（TeamCreateTool 设的模块变量）
  // 5. sessionId（独立单 agent 会话 fallback）
}
```

**核心共享原理**：同一个 team 的所有 agent 解析到同一个 `taskListId`（team name），所以自动读写同一个 `~/.claude/tasks/{teamName}/` 目录。

### Mailbox 通知（任务分配）

```typescript
// TaskUpdateTool.ts:277-298
if (updates.owner && isAgentSwarmsEnabled()) {
  const assignmentMessage = {
    type: 'task_assignment',
    taskId: task.id,
    subject: task.subject,
    description: task.description,
    assignedBy: currentAgentName,
    timestamp: Date.now(),
  }
  await writeToMailbox(updates.owner, assignmentMessage)
  // 写文件到 ~/.claude/mailbox/{agentName}.jsonl
  // 对方 agent 下次心跳时会读到
}
```

**意义**：任务分配不是静默改文件，而是主动通知对方。

### Verification Nudge（验证提示）

```typescript
// TaskUpdateTool.ts:333-349
if (
  status === 'completed' &&
  allTasksCompleted &&
  tasks.length >= 3 &&
  !tasks.some(t => t.subject.includes('verif'))
) {
  result.verificationNudgeNeeded = true
}

// 在 tool result 里追加提示：
// "All tasks completed. Consider spawning a verification agent..."
```

**意义**：所有任务完成时，提示 LLM 生成验证 agent 做最终检查。

### 清理机制（三层）

| 层级 | 触发 | 行为 |
|------|------|------|
| Teammate 死亡 | `unassignTeammateTasks()` | 该 teammate 的所有未完成任务 → owner 清空、status 重置为 pending |
| Team 删除 | `TeamDeleteTool` | 拒绝删除（如果有活跃成员）→ 删 config + task 目录 |
| Session 退出 | `registerTeamForSessionCleanup` | 自动清理孤立的 team 目录 |

---

## Runtime Task：后台进程管理

这是第三套系统，和项目管理无关，纯粹是管理后台进程的。

### 数据模型

```typescript
// src/Task.ts
TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'killed'

TaskStateBase = {
  id: string              // 前缀 + 8位随机（b=bash, a=agent, r=remote...）
  type: TaskType          // 'local_bash' | 'local_agent' | 'remote_agent' | ...
  status: TaskStatus
  description: string
  startTime: number
  endTime?: number
  outputFile: string      // 输出 spill 到磁盘的路径
  outputOffset: number    // 已读偏移
  notified: boolean       // 是否已通知 LLM
}
```

### 状态机

```
spawn → pending → running → completed (exit code 0)
                          → failed (exit code != 0)
                          → killed (stopTask() 调用)
```

### 存储方式

- 纯内存 `AppState.tasks: Map<string, TaskStateBase>`
- 输出超过 8MB 自动 spill 到磁盘
- 终态任务（completed/failed/killed）在通知后自动驱逐

### 我们 Engine7 的现状

我们搬了这套（`engine/src/tools/task-manager.ts`），行为基本一致：
- ID 格式一模一样（`b`/`a` + 8位）
- 状态枚举一模一样（5个）
- 通知 XML 格式字节级兼容
- 区别：我们用 `pendingNotifications` 队列轮询，CC 用 `enqueuePendingNotification` → messageQueueManager

---

## 我们 Engine7 搬了什么、没搬什么

### 搬了（几乎逐行）

| CC 源码 | Engine7 对应 |
|---------|-------------|
| V1 TodoWrite | `TodoWriteTool`（内存，3 状态） |
| V2 Task CRUD | `engine/src/utils/tasks.ts`（磁盘，3+1 状态） |
| Runtime Task | `engine/src/tools/task-manager.ts`（内存，5 状态） |
| sanitizePathComponent | 一模一样 |
| .highwatermark 文件 | 一模一样 |
| findHighestTaskId 逻辑 | 一模一样（但用 sync readdirSync） |
| createTask 流程 | 一模一样（但用内存 withTaskLock） |
| deleteTask 级联 | 一模一样 |
| blockTask 双向更新 | 一模一样 |
| claimTask 守卫 | 一模一样（但没有 busy-check 变体） |
| unassignTeammateTasks | 一模一样 |
| getAgentStatuses | 一模一样 |

### 故意没搬

1. **proper-lockfile**（跨进程文件锁）→ 我们用内存 mutex（`withTaskLock`，Promise 链模式）。单进程不需要文件锁，这是正确的简化。
2. **claimTaskWithBusyCheck** → 我们没有这个变体
3. **createSignal/onTasksUpdated 通知** → 不需要跨进程 UI 订阅
4. **Zod 验证** → CC 每次读都做 safeParse，我们直接 JSON.parse 信任文件
5. **Legacy 迁移**（open→pending 等）→ 我们没有历史数据

### 还缺什么（可能需要补）

1. **Hook 系统**：CC 有 TaskCreated 和 TaskCompleted hooks，可以阻止创建/完成。我们没有。
2. **Mailbox 通知**：任务分配时写 mailbox 文件唤醒 teammate。我们没有。
3. **Verification nudge**：所有任务完成时，CC 会提示 LLM 生成验证 agent。我们没有。
4. **auto-owner on in_progress**：swarm 模式下 pending→in_progress 自动设 owner。我们没搬这个逻辑。

---

## 对 Engine7 团队任务管理的建议

### 短期（现在就能做）

1. **补 auto-owner**：`TaskUpdateTool` 里 pending→in_progress 时自动设 owner，防止两个 agent 同时做一个任务
2. **补 verification nudge**：所有任务完成时提示验证

### 中期（团队模式上线时）

3. **加 Mailbox**：任务分配时通知对方，不要静默改文件
4. **加 Hook 守卫**：至少 TaskCompleted hook，让外部可以拒绝完成（比如测试没过）

### 长期（多进程部署时）

5. **换 proper-lockfile**：如果 Engine7 变成多进程（比如每个 agent 一个进程），内存 mutex 不够用，得换文件锁

---

## 关键文件索引

| 文件 | 用途 |
|------|------|
| `src/Task.ts` | Runtime Task 状态、ID 生成、TaskStatus 枚举 |
| `src/utils/tasks.ts` | V2 Task CRUD + claim + team 集成（核心文件） |
| `src/utils/todo/types.ts` | V1 TodoItem schema（已被 V2 替代） |
| `src/tools/TaskCreateTool/TaskCreateTool.ts` | 创建任务 + TaskCreated hooks |
| `src/tools/TaskUpdateTool/TaskUpdateTool.ts` | 更新/删除/分配 + TaskCompleted hooks + mailbox |
| `src/tools/TaskListTool/TaskListTool.ts` | 列出任务（过滤 _internal、解析 blockedBy） |
| `src/tools/TaskGetTool/TaskGetTool.ts` | 获取单个任务详情 |
| `src/utils/swarm/teamHelpers.ts` | Team config 文件 CRUD |
| `src/utils/teammateMailbox.ts` | 跨 agent mailbox 通信 |
| `src/utils/task/framework.ts` | Runtime task 注册、轮询、驱逐 |
| `src/utils/hooks.ts` | Hook 系统（TaskCreated/TaskCompleted） |

---

## SendMessage：Agent 间通信系统

### 核心发现：完全双向的 peer-to-peer 通信

CC 的 SendMessage 工具（`src/tools/SendMessageTool/SendMessageTool.ts`，918行）支持**任意 teammate 之间互相通信**，不只是 leader→teammate 的单向通知。

### 寻址方式

| `to` 值 | 含义 | 方向 |
|---------|------|------|
| `"researcher"` | 按名字发给 teammate | 任意 agent → 任意 teammate |
| `"*"` | 广播给所有 teammate | 任意 agent → 所有其他 teammate |
| `"team-lead"` | 发给 leader | teammate → leader |
| `"uds:/path/to.sock"` | Unix Domain Socket | 跨 session（同机器） |
| `"bridge:session_..."` | Remote Control | 跨机器 |

**关键证据**：`handleMessage()` 里**没有检查发送者必须是 leader**。发送者名字通过 `getAgentName()` 解析，任何 teammate 都能调 `writeToMailbox(recipientName, ...)` 发给任何其他 teammate。

### 传输层：两种模式

**Tmux 模式（文件 mailbox）**：
```
~/.claude/teams/{team_name}/inboxes/{agent_name}.json
```
- 每个 agent 有自己的 inbox 文件
- `useInboxPoller` 每 1 秒轮询一次
- 任何 teammate 都能写任何 teammate 的 inbox

**In-process 模式（内存队列）**：
- `agentNameRegistry` 直接路由
- `queuePendingMessage()` 直接投递到目标 agent 的消息队列
- 目标 agent 正在运行 → 消息排到下一轮工具调用
- 目标 agent 已停止 → `resumeAgentBackground()` 重启它

### 数据平面 vs 控制平面

**数据平面（纯文本消息）：完全对称**
- 任何 teammate 都能给任何其他 teammate 发消息
- 支持广播（`to: "*"`）
- 没有角色检查

**控制平面（结构化协议消息）：有方向限制**

| 消息类型 | 方向 | 用途 |
|---------|------|------|
| `shutdown_request` | leader → teammate（惯例） | 请求 teammate 关停 |
| `shutdown_response` | teammate → leader（**强制**） | 同意/拒绝关停 |
| `plan_approval_request` | teammate → leader | 请求审批计划 |
| `plan_approval_response` | leader → teammate（**强制**） | 审批/拒绝计划 |
| `permission_request` | teammate → leader | 请求工具权限 |
| `permission_response` | leader → teammate | 授予/拒绝权限 |
| `task_assignment` | leader → teammate | 分配任务 |
| `idle_notification` | teammate → leader | 报告空闲 |

唯一**硬编码**的方向限制是 `shutdown_response`：
```typescript
// SendMessageTool.ts:698-703
if (input.message.type === 'shutdown_response' && input.to !== TEAM_LEAD_NAME) {
  return { result: false, message: 'shutdown_response must be sent to "team-lead"' }
}
```

### 通信架构图

```
┌────────────────────────────────────────────────────────────────┐
│                     完全双向（纯文本）                          │
│                                                                │
│   Team Lead ◄──────── SendMessage ────────► Teammate A         │
│       │            (纯文本)                    │                │
│       │                                        │                │
│       ▼                                        ▼                │
│   Teammate B ◄──────── SendMessage ────────► Teammate C        │
│                  (纯文本)                                       │
│                                                                │
│   * 广播: 任意 agent → 所有其他 agent                           │
│   * UDS: 任意 session → 任意本地 session                        │
│   * Bridge: 任意 session → 任意远程 session                     │
├────────────────────────────────────────────────────────────────┤
│                     有方向限制（结构化消息）                     │
│                                                                │
│   shutdown_request:         leader → teammate（惯例）           │
│   shutdown_response:        teammate → leader（强制）           │
│   plan_approval_request:    teammate → leader                   │
│   plan_approval_response:   leader → teammate（强制）           │
│   permission_request:       teammate → leader                   │
│   permission_response:      leader → teammate                   │
│   task_assignment:          leader → teammate                   │
│   idle_notification:        teammate → leader                   │
└────────────────────────────────────────────────────────────────┘
```

### 我们 Engine7 的现状

我们搬了 SendMessage 工具，支持 teammate 间通信。但传输层和 CC 不同：
- CC 用文件 mailbox + 1秒轮询（tmux 模式）或内存队列（in-process 模式）
- 我们用 `msg_send` 工具直接投递（Discord/飞书/微信通道）

CC 的设计哲学是：**数据平面对称（谁都能聊），控制平面非对称（leader 有特权）**。

---

## 总结

Claude Code 的 Task 系统分三层：
1. **V1 TodoWrite**：轻量内存待办，compaction 就丢
2. **V2 Task**：项目级任务，磁盘持久化，支持团队协作、依赖管理、Hook 守卫、Mailbox 通知
3. **Runtime Task**：后台进程管理，和项目管理无关

加上 **SendMessage**：完全双向的 agent 间通信系统，数据平面对称、控制平面非对称。

我们 Engine7 三套 Task 都搬了，SendMessage 也搬了，但 V2 的团队特性（auto-owner、mailbox 通知、verification nudge、hooks）还没补。这些是团队模式上线前必须做的。
