# Calendar × Nudge × Session-State 整合方案

> 2026-07-01 小柯设计，翀哥确认方向
> 更新：2026-07-01 12:45 Phase 3+4 完成

## 核心架构

```
calendar（持久化）         ← 唯一任务源头
  ├─ add-task → notification → LLM 按 SOP 同步
  ├─ nudge 查 due-reminders → 到期提醒
  └─ nudge 查 stale → 没进展催

SESSION-STATE（内存）       ← compaction 恢复用的工作快照
  ├─ 当前在做什么（- [~]）
  ├─ 💭 感觉 / inner-voice
  └─ 📝 最近消息
  （过渡期仍记录任务，最终不再记录 - [ ] 待办）

nudge                       ← 中间人，只管催
  ├─ tick 读 calendar due-reminders → 到期注入
  └─ tick 读 SESSION-STATE → stale 催促
```

## 已完成

### Phase 1-2: Calendar Schema + Task 类型 ✅

- calendar_mgr.py 加 task 类型（强制 `日期 + HH:MM`）
- remind_before_min（默认60min）/ remind_at（自动计算）/ reminded（标记）
- schema 自动迁移（ALTER TABLE，旧 DB 不用删）
- due-reminders / mark-reminded 命令
- 两个 workspace 都同步了

### Phase 3: Add-Task Notification ✅ (7/1)

**方案：B — 给 ToolUseContext 注入 dispatcher**（翀哥选）

**流程：**
```
LLM 执行 calendar add-task
  ↓
calendar_mgr.py 写入 DB
  ↓
calendar tool handler 调 dispatcher.submitMessage()
  ↓
注入 main session（source=system, priority=later）
  ↓
idle 时触发新 turn，LLM 收到 [task-created] notification
  ↓
LLM 按 SOP 同步到 SESSION-STATE / TodoWrite
```

**改动文件：**
- `handle-query.ts` — HandleQueryDeps 加 `dispatcher` 字段 + toolContext 注入
- `engine-startup.ts` — dispatcher 创建后 `deps.dispatcher = dispatcher`
- `calendar.ts` — 加 `add-task` action + 成功后 submitMessage notification

**测试结果：** ✅ notification 成功注入 main session，走 dispatcher idle 触发

### Phase 4: Nudge 联动 Calendar ✅ (7/1)

**nudge tick 逻辑：**
```
每 5 分钟：
  1. cooldown 检查
  2. 查 calendar due-reminders
     → 有到期 → 注入 [calendar-reminder] + mark-reminded + return
     → 无到期 → 继续
  3. 读 SESSION-STATE → 解析活跃任务
  4. shouldNudge() → progress / urgent / stale / skip
  5. 注入 nudge prompt
```

**改动文件：**
- `nudge/plugin.ts` — 加 `checkDueReminders()` 方法 + tick 里插 due-reminders 查询

**测试结果：** ✅ calendar_mgr.py due-reminders 正常返回，无报错。实际提醒需等任务时间前60min触发。

### Nudge Bug 修复 ✅ (7/1)

- **maxNudge 对 blocked 任务不生效**：shouldStaleWithBackoff 不检查 maxNudge，导致超过上限后无限催
- **修复**：shouldStaleWithBackoff 加 maxNudge 参数，超了返回 'skip'

## 待实现

### Phase 5: 过渡——SESSION-STATE 退化为恢复快照

**目标：** SESSION-STATE 不再记录 - [ ] 待办，只记录当前工作状态。

**过渡步骤：**
1. notification 机制跑稳（Phase 3）✅
2. nudge 联动跑稳（Phase 4）✅
3. compaction 恢复时读 calendar pending tasks 重建"当前任务"
4. SESSION-STATE 删除任务记录区域

**这步不急，等前面的机制都验证通过再说。**

## 已知问题（待修）

1. **nudge 不读子行 blocked 标记** — SESSION-STATE 子行的 `→ [!]` 不被 session-state-reader 解析，只有主行 `- [~]`/`- [!]` 被读到。Workaround：在主行标 `- [!]`。
2. **judgeReason 把"等爹忙完"判成 deadline 而不是 accept** — LLM 判断不够准确，可能需要调 prompt。

## 改动文件清单

| 文件 | 改动 |
|------|------|
| `handle-query.ts` | HandleQueryDeps 加 dispatcher + import + toolContext 注入 |
| `engine-startup.ts` | deps.dispatcher = dispatcher（L699） |
| `tools/calendar.ts` | 加 add-task action + submitMessage notification |
| `nudge/plugin.ts` | 加 checkDueReminders() + tick 里插 calendar 查询 |
| `nudge/judge.ts` | shouldStaleWithBackoff 加 maxNudge 检查 |

## 和 SOP 的关系

- add-task 是加任务唯一入口 → 强制带时间
- notification 触发后 LLM 按 SOP 同步
- SOP 定义"任务写到哪"的规范不变
- nudge 不参与写入，只管催
