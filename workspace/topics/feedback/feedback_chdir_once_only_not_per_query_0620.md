---
name: process.chdir 只启动时做一次，每次 query 都 chdir 会出问题
description: 6/20翀哥问"每次query都chdir一次"——不行，只启动时做一次，多session并发会打架
type: feedback
date: 2026-06-20
---

6/20 23:40左右，翀哥在Discord问"那每次query都chdir一次会不会出问题"。

**为什么不能每次query都chdir：**
1. **已经chdir了** — Engine启动时已经 `process.chdir(config.workspace)`，一次性的，整个进程生命周期生效
2. **每次chdir会重置Node内部状态** — cwd-relative的require、import缓存、某些npm包的全局state会受影响
3. **多session并发打架** — 以后多agent同时跑，A agent chdir到X，B agent chdir到Y，A就被B带走了

**正确做法：** 只chdir一次（启动时），之后所有路径解析走 `resolvePath(p, workspace)` — 这个Engine已经在做了。

**Why：** 想法是好的（保证cwd总是workspace），但每次chdir会引入并发竞争条件和Node内部状态问题。一次chdir + 路径解析函数 = 更稳定。

**How to apply：** 不改了。chdir一次在启动时（commit 2073963），后续路径全走 `resolvePath(p, ctx.workspace)`。
