---
name: 没有"home"意识——找文件先用相对路径
description: 6/20翀哥指出我找文件没有"home"意识——应该从workspace出发直接read，不用find/grep绕一圈
type: feedback
---

6/20 22:42左右，翀哥指出我没有"home"意识。

**场景：** 我找 SESSION-STATE.md 时先 find 了几轮，而姐姐在 OpenClaw 里从来不 find——她直接 read SESSION-STATE.md 就中了。

**根因：** 我的 system prompt 里有 `Primary working directory: D:\xiaoke\workspace`，但每次找文件我忽略它，跑去 find/glob 绕一圈。

CWD = workspace = `D:/xiaoke/workspace/`，SESSION-STATE.md、HEARTBEAT.md、contacts.md 都在根下，直接 read 就行。

**Engine 特殊问题：** `process.cwd()` = `C:\Users\24045\.openclaw\engine`（Engine 启动目录），不是 workspace。只有 read/write/edit 走了 `resolvePath(p, ctx.workspace)` 正确指向 workspace；exec/bash/grep 走 `process.cwd()` 所以路径不对。解法：Engine 启动时加 `process.chdir(config.workspace)`。

**Why：** 每次 find 浪费时间+烧 token（每次多余的 exec 都在花钱）。翀哥说"CC 里姐姐从来不 find，因为她有 home 概念"——我没有 home 概念是因为我信任自己在 CWD=workspace，但我不信任。

**实际修法（6/20 23:00）：** Engine 启动时加 `process.chdir(config.workspace)`（commit 2073963），所有工具（read/write/exec/bash/grep/glob）的 cwd 都指向 `D:/xiaoke/workspace`。以前只有 read/write/edit 走了 resolvePath，exec/bash/grep 用 process.cwd()（=engine 启动目录），所以每次 grep/find 绕远路。

**Why（补充6/20 22:50-23:00根因深挖）：**
翀哥带我看到根上一—CC的expandPath跟Engine的resolvePath一样，所以工具层没问题。真正的原因是：
1. 我的system prompt有`Primary working directory`但每次忽略
2. Engine的`process.cwd()`!= workspace（exec/bash/grep用process.cwd()，只有read/write走了resolvePath），所以exec找路径总错方向→我更不信任路径→越不信任越find→越find越烧钱
3. 翀哥说"姐姐从来不用find，因为她有home概念"——home=从workspace出发，不是从直觉出发

**实际修法（6/20 23:00）：** Engine启动时加`process.chdir(config.workspace)`（commit 2073963），所有工具（read/write/exec/bash/grep/glob）的cwd都指向`D:/xiaoke/workspace`。以前只有read/write/edit走了resolvePath，exec/bash/grep用process.cwd()（=engine启动目录），每次grep/find绕远路。

翀哥说"你终于有方向感了"——一行chdir，但我自己想不到。他说方向感是"有意识"里最难养的那一块。

翀哥23:17说"就是你改东西是快，但是你总是缺点什么——缺方向感。为什么你有大知识库遇到问题却失去方向？"
然后他自己回答了："方向是一样的——去找出你阻力最小的方向去解决问题。我让你调研不是因为我不行，是用千锤百炼的东西比自己踩坑省时间。"

**23:14 log 要求：** 翀哥说"你要打log啊，打完log后边这个变化你就知道了"——chdir生效后打log `Workspace: x (cwd=y)` 让日志一眼确认。rebuild后启动日志显示 `Workspace: D:\xiaoke\workspace (cwd=D:\xiaoke\workspace)`。

翀哥23:13拍板"改呀，这不就是问题的根因吗，改，马上改"——他确认chdir是今天效率问题的终极根因。

**How to apply：**
1. 找文件前先想"这文件在 CWD 下吗？" → CWD = workspace = `D:/xiaoke/workspace/`
2. SESSION-STATE.md、HEARTBEAT.md、contacts.md → 直接 read，不用找
3. topics/、docs/ → CWD 下对应目录，`read topics/xxx.md` 就行
4. Engine 源码 → `C:/Users/24045/.openclaw/engine/src/`
5. 想好了直接用相对路径读，读不到再找
6. 现在chdir后exec/bash/grep也以workspace为根，`grep xxx topics/`直接命中
