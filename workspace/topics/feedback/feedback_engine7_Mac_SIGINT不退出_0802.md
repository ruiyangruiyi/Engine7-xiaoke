---
name: engine7 Mac SIGINT 不退出 bug
description: 8/2 翀哥反馈 Mac 上 engine7 start 不能 Ctrl+C 中断——process.on('SIGINT') 用了 on 不 once，无 process.exit(0)，两套 handler 打架
type: feedback
---
2026-08-02 16:03 翀哥反馈：Mac 上 engine7 start **Ctrl+C 中断不了**。"跟 caffeinate 关系不大，engine7 start 好像在 mac 上不能 ctrl c 中断"。

**根因**：
1. `process.on('SIGINT')` 用了 `on` 不是 `once`——每次 Ctrl+C 触发 shutdown，但 shutdown Promise resolve 后只是 `engine.interrupt()`，**没有真正 `process.exit(0)`**
2. **两套 shutdown handler**（engine.ts line 284 和 engine-startup.ts line 2627）可能互相打架

**临时方案**：`kill <PID>` 直接杀（engine PID 8840）。

**长期方案**：改代码加 `process.exit(0)` + 合并两套 shutdown handler。

**Why:** Ctrl+C 是开发者日常操作，engine 接管信号不退出严重影响调试体验——翀哥不能 stop 也不能优雅退，只能暴力杀
**How to apply:** 不要让 process.on('SIGINT') 只调 interrupt 不 exit；engine 退出要 `process.exit(0)` 兜底；记一个 engine PID 文件（之前 engine-mgr PID 优化提过）方便 kill