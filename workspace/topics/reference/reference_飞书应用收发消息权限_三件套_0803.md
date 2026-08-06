---
name: 飞书机器人收发消息权限三件套
description: 8/3 Amy 装好 engine7 后发消息没回复，根因是飞书应用缺 im:message.send / im:message.send_as_bot 权限——光拿到 App ID/Secret 不等于能收发
type: reference
date: 2026-08-03
---

# 飞书机器人收发消息权限三件套（8/3 Amy 案例发现）

**结论：** 飞书机器人光拿到 App ID/Secret + 跑了 engine7 + feishu Connected **不等于能收发消息**——还需要在飞书开放平台开通消息权限并发布版本。

**收消息要开的权限：**
- `im:message.group_at_msg` — 默认权限，只推 @机器人的群消息
- `im:message.group_msg` — **敏感权限**，收全群消息，需管理员审批
- 私聊消息也需要单独权限（具体 scope 不确定）

**发消息要开的权限：**
- `im:message.send` — 发送消息权限（基础）
- `im:message.send_as_bot` — 以机器人身份发消息权限

**Why：** 8/3 凌晨 Amy 的 engine7 在 Windows 端跑起来，日志全绿（`feishu Connected (mode: websocket)` / `1/1 adapter(s) started` / `ws client ready`），但 Amy 给机器人发消息没回复——根因是飞书应用后台没开通 im:message.send / im:message.send_as_bot。

**How to apply：**
- 飞书机器人部署后发消息没反应，先排查这个权限三件套（group_at_msg / group_msg / message.send / message.send_as_bot）
- **权限管理页面有两个 tab**：左边的 **"应用身份权限"**（不需要审核，开通即用）和右边的 **"用户身份权限"**（需管理员审核，机器人发消息场景用不到）——小白用户默认会点到"用户身份权限"被审核卡住，教程必须明确"在应用身份权限 tab 里搜 im:message"
- 权限搜索结果太多时点 **"查看全部"** → 一次性勾选所有要开的权限（im:message / im:message:send_as_bot）批量处理，比一个一个搜快
- 权限开通后**必须重新发布一个版本**（版本管理与发布 → 创建版本 → 发布），光勾选权限不发布不生效；版本号随便填 1.0.1 即可
- 发布后等 1-2 分钟生效
- **批量开通权限技巧**（8/3 Amy 实践）：飞书后台 → 权限管理 → **批量导入/导出权限** → 贴 JSON 一次性开多个，比一个一个搜开通快
  ```json
  {
    "tenant": ["im:message", "im:message.p2p_msg:readonly", "im:message.group_at_msg:readonly", "im:message.group_msg:readonly", "im:message.send"],
    "user": [], "app": []
  }
  ```
  注意 scope 字段不是 scope 路径，要按飞书后台"权限管理"里展示的 scope 字符串写（如 `im:message.p2p_msg:readonly` 而不是 `im:message` 那种）
- #132（8/5）把 feishu-bot-bootstrap 集成进 init 流时要**自动开这三件套权限 + 自动发版本**——Amy 这种用户不可能自己跑后台
