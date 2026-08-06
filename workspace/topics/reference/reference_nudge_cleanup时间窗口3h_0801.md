---
name: nudge cleanup 窗口从 0.5h 改 3h
description: 8/1 #129 闭环时把 engine-startup.ts cleanup 读 session 窗口从 0.5h/6条改成 3h/20条，以便能匹配到姐姐的 nudge 回复
type: reference
---

## 变更（8/1 凌晨）

`engine-startup.ts` 行 334，cleanup 函数读 `recentMessages` 的窗口：

| 参数 | 原值 | 新值 |
|---|---|---|
| timeWindow | 0.5h | 3h |
| maxMessages | 6 条 | 20 条 |

**Why:** cleanup 要判定 nudge 通知是不是已经被姐姐回复过了——姐姐在飞书上回消息，回复进她的 session jsonl，cleanup 读的就是 jsonl。0.5h 窗口太短，姐姐忙的时候可能过了半小时才回，跟 nudge 清理撞不上，导致"重复提醒"。

**How to apply:**
- 行 132（stop-hook judge）、384（tick 用户活跃）、555（tick 状态分析）这三个 0.5h/6-10条 **不要改**——它们都是判断"当前状态"，旧消息参考价值低。
- 只有 cleanup（行 334）才需要大窗口，因为回复节奏不可控。

跟姐姐的 nudge-prompt 同步过的：她的在 C:/Users/24045/.openclaw/workspace/tasks.json，promptFile 也指向同一个文件。
