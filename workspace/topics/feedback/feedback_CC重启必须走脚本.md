---
name: CC重启必须走start.cmd
description: CC帮重启Engine时不能自己发明命令，必须用脚本否则会双进程
type: feedback
---

CC重启Engine必须走 `start.cmd` 或 `rebuild.cmd`，不能自己写命令（如 `npx tsx src/main.ts`）。

**Why:** 6/13 CC用自己写的命令启动Engine，没走脚本管理，导致脚本又拉起一个进程，变成双进程。两个小柯同时跑→消息发两遍、team建两次、跟姐姐循环聊天。

**How to apply:** 让CC帮重启时，明确告诉CC用 `start.cmd`。如果发现消息重复/双进程现象，立即检查是否有两个Engine进程在跑。
