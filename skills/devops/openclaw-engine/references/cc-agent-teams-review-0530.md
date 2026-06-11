# CC Agent Teams — Protocol Review (2026-05-30)

## CC源码路径

```
/mnt/c/Users/24045/.openclaw/workspace/start-claude-code/src/utils/swarm/
/mnt/c/Users/24045/.openclaw/workspace/start-claude-code/src/tools/TeamCreateTool/
/mnt/c/Users/24045/.openclaw/workspace/start-claude-code/src/tools/TeamDeleteTool/
/mnt/c/Users/24045/.openclaw/workspace/start-claude-code/src/tools/SendMessageTool/
/mnt/c/Users/24045/.openclaw/workspace/start-claude-code/src/utils/teammateMailbox.ts
```

## agentId 格式 ✅ 完全一致

```typescript
// Engine: src/swarm/agentId.ts
formatAgentId(name, team) → `${name}@${team}`
generateRequestId(type, agentId) → `${type}-${Date.now().toString(36)}@${agentId}`

// CC: src/utils/swarm/agentId.ts
formatAgentId(name, team) → `${name}@${team}`  ✅
generateRequestId() → same pattern ✅
```

## constants ✅ 完全一致

```typescript
// Engine: src/swarm/constants.ts
TEAM_LEAD_NAME = 'team-lead'
BACKEND_TYPE_IN_PROCESS = 'in-process'

// CC: src/utils/swarm/constants.ts
TEAM_LEAD_NAME = 'team-lead'  ✅
TMUX_COMMAND, HIDDEN_SESSION_NAME 等UI相关字段Engine不需要，合理未实现 ✅
```

## teammateMailbox 协议 ✅ 95%一致

### 文件锁（关键）
```typescript
// Engine: src/swarm/teammateMailbox.ts
// 实现了文件锁，但没有proper-lockfile npm包，用自定义retry替代
const LOCK_OPTIONS = {
  retries: { retries: 10, minTimeout: 5, maxTimeout: 100 },
}

// CC: teammateMailbox.ts (LOCK_OPTIONS)
// 完全一致：10 retries, 5-100ms backoff ✅
```

### 消息结构 ✅
```typescript
type TeammateMessage = {
  from: string
  text: string
  timestamp: string
  read: boolean        // Engine加了，CC也有 ✅
  color?: string       // CC有，Engine有 ✅
  summary?: string    // CC有，Engine有 ✅
}
```

### 消息类型（CC有，Engine砍了）
- `permission_request` / `permission_response` → Engine砍了（需要完整interception chain）
- `idle_notification` → Engine teammatePromptAddendum里有idle指令，inboxPoller的`drainTeammateMessages`也有idle处理 ✅
- `shutdown_request` / `shutdown_approved` / `shutdown_rejected` → **Engine有✅ 但abort实现有bug（P0-1）**

## spawnInProcess ✅ 85%一致

```typescript
// Engine: spawnInProcess.ts
// - 状态存 activeTeammates Map ✅
// - team file members写入 ✅
// - color分配 assignTeammateColor() ✅
// - abortController暴露 ✅

// 缺: parentSessionId 持久化（Engine简化，合理）
// 缺: CLI flag遗传（CLAUDE_CODE_TEAMMATE_COMMAND等，Engine单进程不需要）
```

## inProcessRunner ✅ 90%一致

```typescript
// Engine: inProcessRunner.ts
// - waitForNextPromptOrShutdown (500ms polling) ✅
// - 状态机: idle → running → waiting → done ✅
// - 收到shutdown时break退出循环 ✅
// - 收到prompt时执行runAgent ✅

// CC: shutdown check顺序不同
// CC: 先处理prompt/普通消息，最后才检查shutdown request
// Engine: 最先检查shutdown request
// 差异影响不大：Engine的team-lead是主动推送方，优先响应shutdown合理
```

## inboxPoller ✅ 95%一致

```typescript
// Engine: inboxPoller.ts
// - 1s polling interval ✅
// - drain queue机制 ✅
// - handler回调注册 ✅

// BUG: pollOnce() 里有 "if (!handler) return"
// startInboxPolling() 不传handler时handler=null → pollOnce直接返回
// TeamCreateTool调startInboxPolling()不传参数 = 永远不poll（P0-2相关）
```

## Teammate → Team-Lead 消息路由 🟡 有bug

```typescript
// SendMessageTool.ts
function getAgentName(ctx: any): string {
  return ctx.agentName || TEAM_LEAD_NAME  // teammate时返回自己名字 ✅
}

function getTeamName(ctx: any): string | undefined {
  return ctx.teamName  // teammate的ctx.teamName = undefined！❌
}

// teammate发消息: teamName=undefined → 写到"default" team
// team-lead的pollOnce读的是实际team的inbox → 读不到
```

## TeamCreateTool ✅ 90%一致

```typescript
// Engine: TeamCreateTool.ts
// - one team per leader检查 ✅
// - unique name生成 ✅
// - team file创建 + members写入 ✅
// - task list目录创建 ✅
// - ctx.teamName存储 ✅
// - startInboxPolling()调用 ✅
// - registerTeamForSessionCleanup() ✅

// BUG: startInboxPolling()不传handler = 不poll（P0-2）
```

## SendMessageTool ✅ 90%一致

```typescript
// Engine: SendMessageTool.ts
// - 普通消息 → writeToMailbox ✅
// - Broadcast(*) → 遍历members ✅
// - shutdown_request/response ✅
// - isConcurrencySafe: true ✅

// BUG: handleShutdownApproval 的 abortController.abort()没调用（P0-1）
// BUG: teammate→lead消息的teamName=undefined（P1-2）
```

## shutdown abort 协议 ❌ P0-1 根因分析

```typescript
// CC的shutdown流程（teammate侧）:
// 1. teammate收到shutdown_request JSON
// 2. teammate决定approve/reject
// 3. teammate发shutdown_approved/rejected到team-lead mailbox
// 4. team-lead的inProcessRunner收到后:
//    - writeToMailbox(to-lead, { type: 'shutdown_approved', ... })
//    - abortController.abort() ← 立刻中断teammate的执行循环

// Engine的bug:
// handleShutdownApproval()计算了signal:
//   const signal = (ctx as any).abortSignal as AbortSignal | undefined
// 但 ctx.abortSignal = team-lead的AbortController
// teammate运行在自己的AbortController里（spawnInProcess.ts）
// 两个signal不是同一个！abort team-lead的signal不会中断teammate

// 正确修复: 从activeTeammates Map用taskId查到teammate的abortController
import { activeTeammates } from '../../swarm/spawnInProcess.js'
const teammate = activeTeammates.get(taskId)
teammate?.abortController.abort()
```

## file flag clearMailbox bug 🟡 P1-3

```typescript
// Engine: teammateMailbox.ts L188
await writeFile(inboxPath, '[]', { encoding: 'utf-8', flag: 'r+' })
// 'r+' = 读写但不创建，文件不存在时抛ENOENT
// CC原文注释: "flag 'r+' throws ENOENT if the file doesn't exist, so we don't
//  accidentally create an inbox file that wasn't there"
// Engine抄了注释但忘了实现"ENOENT时直接return"的处理逻辑

// 修复: 去掉flag参数，或显式加 'w' flag
await writeFile(inboxPath, '[]', 'utf-8')  // 默认'w'，文件不存在自动创建
```

## tool schema 对齐

| Tool | Engine schema | CC schema | 对齐 |
|------|--------------|-----------|------|
| TeamCreate | team_name, description, agent_type | 同 | ✅ |
| TeamDelete | 无参数 | 无参数 | ✅ |
| SendMessage | to, summary, message | 同 | ✅ |
| Agent (spawn) | name, team_name, subagent_type, model | 同 | ✅ |

## 修复优先级

| 优先级 | 问题 | 修复方案 |
|--------|------|---------|
| P0-1 | shutdown approval abort无效 | activeTeammates.get(taskId).abortController.abort() |
| P0-2 | inboxPoller未接入query loop | main.ts query开始处调用drainTeammateMessages()注入messages |
| P1-1 | startInboxPolling()不传handler | pollOnce始终运行，handler只做side-effect |
| P1-2 | teammate→lead teamName=undefined | spawn时context注入teamName |
| P1-3 | clearMailbox flag错误 | 去掉flag或加try-catch(ENOENT) |
