---
name: Discord DM命令未注册bug
description: Discord命令只在服务器可见，DM不可见；同时注册guild+global解决
type: feedback
---

**问题：** 6/13翀哥发现Discord DM窗口没有注册slash命令（如/reload），但服务器频道里能看到。

**根因：** discord.ts第247-252行：如果配置了guilds，只注册guild命令；没配guilds才注册全局命令。guild命令只在服务器内可见，DM里看不到。

**修复：** 同时注册guild命令（即时生效）和global命令（DM可用，Discord最多1小时缓存延迟）。重启Engine后生效。
