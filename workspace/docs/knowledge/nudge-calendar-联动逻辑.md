# Nudge ↔ Calendar 联动逻辑

> 2026-07-01 小柯整理。Engine commit `0728d81`。

## 一句话

Nudge 每 5 分钟 tick 一次，**先查 calendar 到期提醒，有的话直接注入 main session 并 return**，没有才走 stale/progress 催促逻辑。Calendar reminder 优先级最高。

## Nudge tick 完整流程

```
tick（每5分钟）
  │
  ├─ Step 1: 全局跳过判定
  │    cooldown 内？→ skip
  │    主对话在跑？→ skip
  │
  ├─ Step 2: 查 calendar 到期提醒  ← 联动点
  │    openDb → dueReminders()
  │    SELECT WHERE status='pending' AND reminded=0 AND remind_at <= now
  │    │
  │    ├─ 有到期提醒 → 逐条 markReminded
  │    │    ├─ weekly → 重算下周 remind_at + reminded=0（循环）
  │    │    └─ date/task → reminded=1（一次性）
  │    │  注入 [calendar-reminder] 到 main session → return（不走下面）
  │    │
  │    └─ 无到期提醒 → 继续 Step 3
  │
  ├─ Step 3: 读 SESSION-STATE 找 - [~] / - [!] 活跃任务
  │           没有活跃任务 → skip
  │
  ├─ Step 4: 用户最近活跃？（最近10分钟有 user 消息）→ skip
  │
  ├─ Step 5: shouldNudge → progress / stale / skip
  │
  ├─ Step 5.5: blocked 任务 → LLM 判断理由是否合理
  │            accept → 停止催促
  │            reject/deadline → 继续 stale
  │
  ├─ Step 6: 拼 prompt + 注入 main session
  │
  └─ Step 7: 写 nudge-state.json（per task 计数 + lastAt）
```

**文件位置：** `engine/src/nudge/plugin.ts` → `tick()`

## Calendar 三种类型的 remind 行为

| 类型 | add 命令 | remind_at 计算 | 到期后 markReminded |
|------|---------|---------------|-------------------|
| **task** | `add-task`（必带 time_exact） | 精确时间 - remind分钟 | reminded=1（一次性） |
| **date** | `add`（带 date，无 weekly） | 当天 09:00 - remind分钟 | reminded=1（一次性） |
| **weekly** | `add`（带 weekly + day） | 本周指定日 - remind分钟 | 重算下周 remind_at + reminded=0（每周循环） |

**文件位置：**
- remind_at 计算：`engine/src/calendar/helpers.ts` → `computeRemindAt()` / `computeWeeklyRemindAt()`
- markReminded 逻辑：`engine/src/calendar/commands.ts` → `markReminded()`
- dueReminders 查询：`engine/src/calendar/commands.ts` → `dueReminders()`

## Notification 区分

| 操作 | 触发 notification | 目的 |
|------|------------------|------|
| `add-task` | ✅ `[task-created]` 注入 main session | SOP 同步（写 SESSION-STATE + TodoWrite） |
| `add weekly` | ❌ 静默入库 | 到时间 nudge 自动提醒 |
| `add date` | ❌ 静默入库 | 到时间 nudge 自动提醒 |

**设计意图：** add-task 是"派活"，需要落地到任务追踪系统；weekly/date 是日程记录，到时间 nudge 通知就行，不用写 SESSION-STATE。

## 数据流总结

```
用户 add-task/weekly/date
  │
  ├─ calendar tool handler
  │    INSERT INTO events (..., remind_at, reminded=0)
  │    └─ add-task only → [task-created] notification → main session
  │
  └─ 5分钟后 nudge tick
       dueReminders() → remind_at <= now AND reminded=0
       │
       ├─ 命中 → markReminded → [calendar-reminder] → main session
       │         小柯收到后判断该不该 msg_send 提醒翀哥/姐姐
       │         calendar done <id>
       │
       └─ 未命中 → 走 stale/progress 催促逻辑
```

## DB schema（events 表）

```sql
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,         -- 'weekly' | 'date' | 'task'
  status TEXT DEFAULT 'pending',  -- 'pending' | 'done' | 'archived'
  event TEXT NOT NULL,
  day TEXT,                   -- weekly: '周一'~'周日'
  time TEXT,                  -- weekly: '14:00' | '全天'
  date_str TEXT,              -- date/task: '7/5' | '5/26-29'
  time_exact TEXT,            -- task: '14:00'
  remind_before_min INTEGER DEFAULT 60,
  remind_at TEXT,             -- ISO UTC，到期触发
  reminded INTEGER DEFAULT 0, -- 0=未提醒 1=已提醒
  created_at TEXT,
  done_at TEXT,
  archived_at TEXT
)
```

**DB 位置：** `workspace/.calendar/calendar.db`
