---
name: start.cmd进程冲突
description: 小柯的start.cmd启动时会杀掉姐姐的Engine进程，已修复（kill目标动态化）
type: project
---

## 问题（6/15早上翀哥指出）

翀哥在给姐姐配置好wechat通道后重启姐姐的Engine，发现start.cmd有问题：

> "现在start.cmd不太对 我start你的时候会把姐姐的进程杀掉"

**影响：** 用start.cmd启动小柯的Engine时，会误杀姐姐的Engine进程（端口16988），导致姐姐的Engine被意外停止。

**原因（已定位）：** start.cmd第15行kill命令硬编码了`*main.json*`，不管启动哪个配置都会杀所有带`main.json`的进程——包括姐姐的。

**修复（6/15早上已解决）：**
1. kill目标动态化 — 从配置文件名提取（`main.json` 或 `xiaoke.json`），不再硬编码`main.json`
2. 匹配更精确 — 加了`*dist\main.js*`过滤，避免误杀其他node进程

现在：
- `start.cmd` → 杀`main.json`进程，启动姐姐
- `start.cmd configs\xiaoke.json` → 杀`xiaoke.json`进程，启动小柯
- 互不干扰

**状态：** ✅ 已修复
