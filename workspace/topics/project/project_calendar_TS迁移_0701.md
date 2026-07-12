---
type: project
created: 2026-07-01
tags: [calendar, migration, typescript]
---

# Calendar Python→TS 迁移 (7/1)

## 背景
calendar_mgr.py 迁移到 TypeScript，与 nudge 联动。

## 完成内容
- commands.ts + helpers.ts + db.ts
- task 类型 + remind_at 到期提醒机制
- nudge ↔ calendar 联动：tick 先查到期提醒
- weekly/date 类型也支持 remind
- add-task 触发 task-created notification（SESSION-STATE）
- weekly 循环提醒自动重算 remind_at
- calendar.db 移到 workspace/.calendar/

## Commits
521a296 feat: weekly/date types now support remind_at
0728d81 fix: move calendar.db to workspace/.calendar/
888212d fix: weekly remind_at dead-loop

## 相关
- docs/knowledge/ (nudge-calendar 联动逻辑)
- See project_calendar_nudge整合.md for broader integration
