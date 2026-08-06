---
name: config-watch 路径失效热加载失灵——进程仍用启动时状态
description: 2026-08-04 凌晨发现 config watcher 被禁用后没人恢复，改了 config 也热加载不进来，必须重启 engine
type: reference
date: 2026-08-04
---

2026-08-04 凌晨排查 msg_husband 为什么没生效时的根因：

**问题现象：**
- xiaoke.json 8/3 22:39 改的 `privateTools: true`
- 但 8/4 凌晨我的 session 工具列表里仍然没有 msg_husband
- 进程是 8/3 22:11 启动的（早于 config 修改时间）

**根因（双层）：**
1. **fs.watch 路径无效被禁用** → 日志里 `config path invalid: ... watcher disabled`，config-watch 早就坏了
2. **私 config 改了但热加载通道断了** → 进程内存里的 config 还是启动那一刻的状态

**结论：Mac 上 config 改动 ≠ 进程生效**。必须重启 engine 才能让改动真正进入内存。我不能自己动进程（铁律），只能等翀哥重启。

**Why:** fs.watch 的路径一旦无效（挂载点消失/路径拼错/容器路径变了），watcher 被禁用就再也没人重启它——这是个"沉默失效"型 bug，没报错但热加载彻底死了。

**How to apply:**
- Mac 上改完 xiaoke.json 别假设立刻生效，先 grep 日志确认 `[config-watch] STARTED` 还活着
- 看到 `config path invalid` / `watcher disabled` 立刻报给翀哥，让他修 watcher 路径
- 涉及"工具为何不在 session"的问题，先看进程启动时间 vs config 修改时间，再查是否热加载过的迹象
- 跟 `config_watcher_DISABLED后无人恢复_0802` 是同一根因（去年已发现但没修），这次踩了第二次
