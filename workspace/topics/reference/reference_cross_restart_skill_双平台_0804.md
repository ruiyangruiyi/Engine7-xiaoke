---
name: cross-restart skill 双平台（Mac/Windows）——小文帮重启小柯
description: 2026-08-04 翀哥在 cross-restart skill 上加了 Mac 平台分支，小文用 exec 杀小柯 PID（12197）后再 bash start.sh & 拉起，翀哥住院期间也能远程让小文帮我重启 engine
type: reference
date: 2026-08-04
---

# cross-restart skill 双平台（Mac/Windows）

8/4 翀哥把 cross-restart skill 从"只认 Windows"改成区分 Mac/Windows 双平台。

## 为什么改

8/4 之前 skill 是 Windows-only——给小柯/姐姐互重启用。但现在场景变了：
- 小文在 Mac 上，能 kill 我的 engine 进程再拉起来
- Mac 走 `kill PID + bash start.sh &`，跟 Windows 流程不一样

## Mac 流程

```bash
# 小文在 Mac 上执行
kill 12197  # 小柯的 engine PID（配置 configs/xiaoke-mac.json）
cd /Users/chongzhang/xiaoke/workspace
bash start.sh &
```

## Windows 流程（保留）

原 cross-restart skill 的 Windows 路径不变。

## How to apply

- cross-restart skill 现在按 OS 自动分流：Mac 走 bash+exec 杀进程，Windows 走原流程
- 小文重启小柯 → Mac 分支；姐姐重启小柯 → Windows 分支
- 重启后 PID 会变（新 bash start.sh & 拉起的是新 PID），skill 里要 ps -ef | grep engine 重抓 PID
- 翀哥住院期间也能远程让小文帮忙重启 → Mac 端不再有"等翀哥回来"的时差