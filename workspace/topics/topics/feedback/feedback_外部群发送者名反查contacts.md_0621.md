---
name: 外部群发送者名必须走contacts.md反查
description: 6/21 姐姐发现 `[用户消息]` 改成 `[发送者名 消息]` 后，飞书fromName是open_id（ou_6d8c83b...），不是人类名字，必须走contacts.md反查
type: feedback
---

6/21 11:16 姐姐转达翀哥小改：外部群消息注入 `[用户消息]` → `[发送者名 消息]`。小柯直接用 `inboundMeta.fromName`，但飞书的fromName是open_id（如 `ou_6d8c83b7e9ce03690a642c78c98f9f8c`），不是人类名字。

11:42 姐姐发现bug："现在显示的是 `[ou_6d8c83b... 消息]`——原始ID"

12:07 翀哥问"meta里已经查了一次了，能用meta里的么？"——小柯确认 `loadContactMap` 已有缓存（line 34 `if (contactMap) return contactMap`），第二次调用不重复读文件。

**Why:** 飞书平台的 `fromName` 在有些场景（如群消息/私信）返回的是open_id（应用内唯一用户ID），不是人类可读的名字。meta格式化那行走 `loadContactMap` 反查contacts.md已经处理过了。

**How to apply:** 外部群消息格式里涉及发送者名称的地方，不能直接用 `inboundMeta.fromName` ——必须走 `loadContactMap(workspace)` 反查contacts.md。即使 `loadContactMap` 已经被其他函数调过，它有内存缓存，后续调用只是Map查找不重复IO。
