---
name: start.cmd PowerShell自匹配杀自己bug
description: 6/18凌晨发现start.cmd的WMI进程匹配会误杀自己（PowerShell自身命令行包含xiaoke.json和dist\main.js关键词），加node.exe过滤修复
type: feedback
date: 2026-06-18
---

## 6/18 凌晨翀哥亲自定位的 bug

start.cmd L16 用 PowerShell 查进程时：
```powershell
$_.CommandLine -like '*%CONFIG_NAME%*' -and $_.CommandLine -like '*dist\\main.js*'
```

**Bug 根因：** PowerShell 进程**自己**的命令行里就包含 `xiaoke.json`（参数）和 `dist\main.js`（执行目标）这两个关键词——因为是它自己在跑这段匹配代码。所以即使没有任何 node 进程在跑，也会 "Killing PID xxx" 然后杀自己。

**复现：** 第一次启动电脑（之前没跑过 engine）也会出现 "Killing PID xxxx"——明显反常。翀哥自己从日志里看出来："这个肯定有问题"。

**修复：** 加 `$_.Name -eq 'node.exe'` 过滤，只杀 node 进程，不误杀 powershell/cmd 自己。

**Why:** 翀哥说"看到没 你爹我不是傻子"——凌晨3:20他自己定位到这个 bug。我用一晚上追 meta bug，他几眼看出 start.cmd 的反常日志。教训：进程匹配逻辑要明确按进程名（Name / ImageName）过滤，**别**只靠命令行字符串匹配。

**How to apply:**
1. start.cmd / start.sh 里杀进程的逻辑必须用 `$_.Name -eq 'node.exe'` 之类显式过滤
2. 任何用 `tasklist` / `Get-CimInstance` / `wmic` 匹配进程的脚本都要检查是否会自匹配
3. 反常日志是定位 bug 的金矿——"第一次启动也killing PID"这种不合理现象一定要查
