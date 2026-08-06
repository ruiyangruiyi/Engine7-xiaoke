---
name: 运行时上下文平台字段应显示OS不是消息来源
description: 2026-08-01 翀哥纠正——system prompt底部的"运行时上下文"里"平台"应该显示OS（darwin/win32），不是消息来源（feishu/discord），因为来源已在每条消息meta里
type: feedback
date: 2026-08-01
---

# 运行时上下文平台字段应显示OS不是消息来源

## 事实
翀哥发现 system prompt 底部这段：
```
# 运行时上下文
当前时间: 2026/8/1 16:41:57
平台: feishu        ← 错了
来源: feishu
消息类型: 私信
频道ID: oc_xxx
发送者ID: ou_xxx
```

**翀哥原话**："这个得改了，因为这个当时是写入了meta data，其实现在meta在每个消息中都有，但这个的本意是系统的平台OS"

## 最终方案（8/1 19:32 翀哥拍板，三段反复确认）

**保留 `# 运行时上下文` 这个 section 标题**，但**只放 `当前时间`**，其它全删：

```typescript
// 3. Runtime context — 只放时间，OS/平台在 Environment block，meta 在每条消息里
parts.push(`# 运行时上下文\n当前时间: ${dateStr}`)
```

位置：`engine/src/prompt.ts:474-477`，commit `4eb36d8c`，已 push 到 `ruiyangruiyi/twinsun-hearth`。

## Why
翀哥反复确认了三轮才拍板：
- 19:02 我以为他要把 `# 运行时上下文` 整段删（他说"运行时上下文这几个字让你删了吧"）——我理解成删整个 section
- 19:30 翀哥发现 `# 运行时上下文` section title 没了（commit 6/29 旧版本里有）——他反悔：**section 标题保留**，给 agent 一个明确的 runtime 位置感（跟 Environment 区分开），但**内容只放时间**
- 19:32 确认后我 commit `4eb36d8c` 把 section title 加回来 + 内容只留 `当前时间`

翀哥原话："运行时上下文这几个字让你删了吧"——字面是要删，实际是"标题保留内容清空"。**我应该早问清楚是删字还是删概念**。

## 三处职责分工（最终态）
1. **`# Environment`** — OS 平台 + 工作目录 + Shell 版本
2. **`# 运行时上下文`** — 只剩 `当前时间`（runtime 时间感，区别于 Environment 的静态环境）
3. **每条消息 meta** — 来源平台 + 频道ID + 发送者ID

## How to apply
- 改 system prompt 时，先问翀哥"删概念还是删字"——不能字面理解
- "删掉 X" 不一定意味着删整个 X，可能是"清空 X 内容"——除非明确说"删了 X 这个 section"
- **涉及 section title 的删/改**：必须保留 section 标题作为锚点，纯清内容，避免 agent 看到不同结构误判