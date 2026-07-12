---
name: 外部群发送者名反查contacts.md
description: 6/21 姐姐发现 `[用户消息]` 改成 `[发送者名 消息]` 后，飞书fromName是open_id（ou_6d8c83b...），不是人类名字，必须走contacts.md反查
type: feedback
date: 2026-06-21
---

6/21 11:16 姐姐让把外部群消息注入格式 `[用户消息]` 改为 `[发送者名 消息]`。

11:42 翀哥发现 bug——meta 那行显示"翀哥"但 `[xxx 消息]` 这行显示 `[ou_6d8c83b7e9ce03690a642c78c98f9f8c 消息]`，原始 open_id。

**根因：** 
- meta（formatWithMeta）走了 `loadContactMap(workspace)` 反查 contacts.md
- senderLabel 直接用了 `inboundMeta.fromName`，但飞书 fromName 本身就是 open_id，不是人类名字
- 飞书 ChannelAdapter 里 fromName 拿的就是飞书 open_id（`ou_` 开头），不是通讯录名

**修复（commit 2017357）：**
- 加 `resolveSenderName(inboundMeta, workspace)` 函数，复用 formatWithMeta 同样的 `loadContactMap` 反查逻辑
- 回复翀哥"能否复用 meta 的结果"时确认：loadContactMap 有缓存（`if (contactMap) return contactMap`），第一次查完后续都是内存 Map 查找，不重复 IO

**How to apply:**
- **飞书相关：** 任何显示发送者名的场景，必须走 contacts.md 反查。飞书 fromName 是 open_id 不是名字。
- **反查有缓存：** loadContactMap 有内存缓存，多次调用不重复读文件，可以放心复用。
