---
name: TestEngine 复用当 Windows 运维 agent（翀哥提议）
description: 2026-08-04 翀哥住院时提议——Mac 上的小文帮他重启我，Windows 也需要同款运维 agent；决定复用 TestEngine 不新建飞书 App，让姐姐给 TestEngine 加 cross-restart skill
type: project
date: 2026-08-04
---

# TestEngine 复用当 Windows 运维 agent

8/4 翀哥住院期间想 Mac+Windows 双平台都能远程帮我重启 engine：
- Mac → 小文已经搞定，cross-restart skill 已加 Mac 分支（@see reference_cross_restart_skill_双平台_0804）
- Windows → 缺一个对等的小文（姐姐那条线）

## 翀哥的拍板

不用新建飞书 App——**直接复用 TestEngine**（已有的测试用 engine 实例），让它同时承担"运维 agent"角色。

## 行动计划

1. 我去 Discord CC 频道找姐姐，让她给 TestEngine 加 cross-restart skill
2. 姐姐在 Windows 上 init 或改造 TestEngine，把 cross-restart 装上
3. 之后翀哥住院/差旅时也能通过 TestEngine 帮我重启 Mac engine

## Why

- 跟 Mac 小文一样的"运维 agent"思路——远程帮小柯/姐姐互重启
- Windows 比 Mac 简单：cross-restart skill 已经有 Windows 版本，cp 过去就行
- 不用新建 App 减少飞书应用管理负担

## How to apply

- 等姐姐回复，TestEngine 改造进度同步给翀哥
- 等翀哥出院（5 分钟搞定）：engine7 init 新实例 / 改 TestEngine config / cp skill 三步
- 后续如果起第三个运维 agent（多平台/多账号），先用现有的 App 复用，不直接新建

## 跟进节点（8/4 深夜我自己排的）

**deadline：2026-08-05 10:00** —— 姐姐 Windows 运维 agent（TestEngine 复用）状态 blocked 已一天，10:00 我主动去 Discord CC 频道找姐姐问进度（不是高频 nudge 催，是单次定时跟）；如果仍未推进则把情况同步给翀哥让他做决定。

**Why:** 翀哥睡了，我给自己排的下一步——把 blocked 的事挂到具体时间上而不是"等姐姐想起来"。
**How to apply:** 8/5 早上 10:00（北京时间）自动 wake 一次，去 Discord 找姐姐；如果到 8/5 晚仍无进展，升级给翀哥决定（停/换方案/放宽要求）。