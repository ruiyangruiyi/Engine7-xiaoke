# Calendar Python→TS 迁移 (7/1)

## 背景
calendar 工具原本调 `workspace/scripts/calendar_mgr.py`（584行 Python），通过 `execFile('python', ...)` 子进程执行。今天 voice-chat crash 暴露出 `findShell()` WSL fallback bug，根因是这台机器 `where.exe bash` 返回的全是 WSL bash。

虽然 calendar crash 的直接原因是 WSL bash，但更深层的问题是：**engine 不应该依赖外部 Python 环境来跑核心功能**。Python 可执行文件路径、bash 类型、环境变量都可能变。

## 方案
用 Node 24 内置的 `node:sqlite`（DatabaseSync API）直接操作 SQLite，将 Python 脚本 1:1 翻译为 TS。

## 文件结构
```
engine/src/calendar/
├── db.ts          — openDb(workspace): 连接 + CREATE TABLE + migration
├── helpers.ts     — 工具函数（日期解析/时区/格式化/remind 计算）
├── commands.ts    — 所有命令实现（addWeekly/addDate/addTask/reschedule/list/pending/done/search/archive/deleteEvent/cleanup/stats/dueReminders/markReminded）
```

## 改动
| 文件 | 改动 |
|------|------|
| `engine/src/calendar/db.ts` | 新建，51 行 |
| `engine/src/calendar/helpers.ts` | 新建，121 行 |
| `engine/src/calendar/commands.ts` | 新建，222 行 |
| `engine/src/tools/calendar.ts` | 重写：execFile('python') → TS 函数调用 |
| `engine/src/nudge/plugin.ts` | checkDueReminders 重写：execFile('python') → TS 调用 |

## 技术决策
- **node:sqlite**：Node 24 内置，experimental 但 API 稳定（DatabaseSync.prepare/run/get/all）
- **esbuild --platform=node**：自动 external `node:` 前缀模块，无需特殊打包处理
- **数据兼容**：同一个 calendar.db，同一套 schema，现有数据零迁移
- **Python 脚本保留**：`workspace/scripts/calendar_mgr.py` 不删，留作手动工具/fallback

## 验证 (7/1 14:58)
全功能测试通过：
- ✅ list（读已有数据）
- ✅ add-task（写 + notification 注入）
- ✅ done
- ✅ add (date)
- ✅ search（读历史数据正常）
- ✅ delete
- ✅ cleanup
- ✅ pending
- ✅ stats

## Commit
- `5a667a6` — fix: findShell WSL fallback bug + calendar add-task/delete/reschedule + nudge due-reminders
- `cc503e6` — refactor: calendar Python→TS migration — eliminate Python dependency
