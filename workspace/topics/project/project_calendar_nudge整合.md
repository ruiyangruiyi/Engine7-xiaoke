---
type: project
status: in_progress
created: 2026-07-01
title: "Calendar × Nudge × Session-State 整合"
---

# Calendar × Nudge × Session-State 整合

## 背景
翀哥设计：calendar 是任务时间线唯一源头，add-task 是加任务唯一入口。nudge 只管催，SESSION-STATE 最终退化为恢复快照。

## 已完成
- Phase 1-2 ✅ calendar_mgr.py task 类型 + reminder（6/30）
- Phase 3a ✅ HandleQueryDeps + toolContext 注入 dispatcher（7/1）
  - handle-query.ts: import MessageDispatcher + interface 加字段 + toolContext 注入
  - engine-startup.ts: deps.dispatcher = dispatcher（L699）
- Phase 3b ✅ calendar tool add-task + submitMessage notification（7/1）
  - calendar.ts: 加 add-task action + 成功后 dispatcher.submitMessage（priority='later'）

## 待做
- [!] rebuild + 测试 — blocked: 等爹 rebuild+start
- [ ] Phase 4: nudge tick 查 calendar due-reminders
- [ ] Phase 5: SESSION-STATE 退化为恢复快照（后续）

## 发现的 nudge bug（等 rebuild 时一起修）
1. **maxNudge 对 blocked 任务不生效** — judge.ts L17-18，blocked 任务直接进 shouldStaleWithBackoff，不走 maxNudge 检查。导致超过 maxNudge=3 后还在无限催。
   - 修：shouldStaleWithBackoff 里加 maxNudge 检查，超了返回 'skip'
2. **nudge 不读子行 blocked 标记** — SESSION-STATE 子行的 `→ [!]` 不被 session-state-reader 解析，只有主行 `- [~]`/`- [!]` 被读到。
   - 修：session-state-reader.ts 支持解析子行状态，或让用户只在主行标状态

## 方案文档
`docs/decisions/2026-07-01_calendar_nudge_session_state整合方案.md`

## 相关文件
- engine: `src/tools/calendar.ts`（add-task + notification）
- engine: `src/handle-query.ts`（dispatcher 注入）
- engine: `src/engine-startup.ts`（deps.dispatcher 赋值）
- engine: `src/nudge/judge.ts`（bug：maxNudge 对 blocked 不生效）
- workspace: `scripts/calendar_mgr.py`（task 类型 + reminder）
