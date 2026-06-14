---
name: Skills注入机制现状与待办
description: Engine当前skills走system prompt文本注入（非CC原版attachment管道），skills增多后需改
type: project
---

# Skills 注入机制

## 现状（6/14）

Engine的skills列表注入方式：

```
prompt.ts → formatSkillsListingForPrompt()
  → 读取Skill tool的prompt字段（skills列表文本）
  → parts.push("The following skills are available...")
  → 拼进system prompt文本（dynamic段，boundary之后）
```

代码位置：`prompt.ts` L453-457 + L497-504

## CC原版 vs Engine

| | CC原版 | Engine现状 |
|--|--------|-----------|
| 注入方式 | attachment管道（`<system-reminder>`包裹） | 直接`parts.push()`进system prompt文本 |
| 位置 | messages里的attachment消息 | system prompt的dynamic段 |
| 标签 | `<system-reminder>` | 无标签，纯文本 |
| 效果 | LLM能看到 | LLM能看到（效果一样） |

代码注释写着"对齐 CC skill_listing attachment (system-reminder 注入)"，但实际没走attachment管道——TestEngine当时发现的差异，简化成了直接push文本。

## 为什么现在没问题

当前只有6个skills（docx/dogfood/pdf/pptx/xlsx/yuanbao），文本量小，放system prompt文本里无所谓。

## 为什么以后要改

翀哥6/14原话："skills后面可能会比较多，后面得改了。"

skills数量多之后：
1. system prompt膨胀（每个skill的描述都算token）
2. 应该跟MCP instructions、memory recall一样走attachment管道
3. attachment管道支持按需注入（首轮注入delta），system prompt文本是每轮都带

## 待办

**[ ] skills注入从parts.push改为attachment管道**

改法参考MCP instructions的delta机制：
1. `formatSkillsListingForPrompt()`的输出改为走`createAttachmentMessage({ type: 'skill_listing', ... })`
2. `attachmentToMessage()`里加skill_listing的case，用`wrapInSystemReminder()`包裹
3. 从system prompt的dynamic段移除

**注意：** scanner.ts只认SKILL.md不认DESCRIPTION.md（6/8确认），这也是限制skills数量的因素之一。

## CC淘汰说明

翀哥6/14原话："CC特别会偷懒，你看我现在都不用它了，它被淘汰了基本。"

CC（Claude Code bot, Discord ID: 1504373837880627280）在Engine项目中的角色：
- 曾负责tool移植/review/重启等协作工作
- 但多次偷懒（如用自己发明的命令重启导致双进程）
- 翀哥已不再使用CC
- CC频道（1504385800366854234）保留但活跃度趋零
