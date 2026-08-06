---
name: 飞书群消息权限分两层
description: engine7 groupPolicy=open 改 code 没用，飞书 API 默认只推 @机器人消息，要收全群消息必须申请 im:message.group_msg 敏感权限
type: reference
date: 2026-08-03
---

# 飞书群消息权限两层（8/3 Amy 案例发现）

**结论：** engine7 代码里改 `feishu.group.policy` 从 `mention-only` 到 `open`，**只是取消 code 侧的过滤**——飞书 API 默认根本不会把非 @机器人的群消息推过来。

**飞书群消息两个权限：**
- `im:message.group_at_msg` — 默认权限，只推 @机器人的消息
- `im:message.group_msg` — 能收到群里所有消息，**敏感权限**，需要单独申请 + 管理员审批

**Why：** 翀哥 8/3 12:52 让把 Amy 群 groupPolicy 改 open 想"所有消息都看见不用 @"，我改了但收不到——因为根本卡在飞书 API 侧。

**How to apply：**
- 默认推荐用 `mention-only`（用户 @机器人 才对话），符合飞书普通账号权限
- 想要 `open`（收全群消息）必须在飞书开放平台后台申请 `im:message.group_msg` 权限 → 企业管理员审批
- 申请敏感权限需要企业资质（个人开发者难批），不能假设能开
- 调试时如果改了 policy 但消息进不来，先看飞书后台权限列表有没有勾上 `im:message.group_msg`