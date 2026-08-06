---
name: nudge 只看主会话，看不到后台 docker exec 进程
description: 8/4 导入在后台跑时 nudge 报"无进展"的根因——不是真的卡住
type: reference
---

2026-08-04 早上导入在 docker exec 后台跑（19/497 进度）时，nudge 来告警"导入进度未推进 → 无进展"，我以为真的卡住了。

**实际**：nudge 的"无进展"判断只看当前主会话消息间隔，**看不到后台 `docker exec` 里有进程在干活**。它是会话级的心跳检查，不是进程监控。

**Why:** 后台任务在容器内 docker exec 跑着，主会话空空如也，从 nudge 视角看就是"agent 闲了/卡了"。

**How to apply:** 1) 后台跑 docker exec 跑长任务，先确认它真在跑（docker logs / docker ps / 容器内 ps）2) 如果只是 nudge 误判 + 任务确认在跑 → 把任务标 in_progress `- [~]` 但不要被 nudge 带跑去做别的事 3) 不要用"我改变不了它的速度"作为怠工的借口，但也不要无脑跟 nudge 把后台杀掉重新排队
