---
name: 实现文档落地约定——docs/design/ 不是 topics/
description: 6/21翀哥指出实现文档应写docs/design/而非topics/，已约定docs管方案→实现全生命周期，topics只放auto memory摘要
type: feedback
date: 2026-06-21
---

6/21 11:00 翀哥检查我工作流程时发现：

我把口罩Agent的完整实现文档写到了 `topics/project/project_口罩Agent_0621.md`（auto memory 领地），但 AGENTS.md 说 topics/ 是"别动"的。同时 `docs/design/2026-06-21_口罩Agent实现方案.md` 也有一份方案。**重复了，而且放错了地方。**

**Why：** 我混淆了两类文档的职责：
- `topics/` = auto memory 自动提取的摘要（短、精、结构固定）
- `docs/` = 我手动维护的知识文档（全、可读、适合人类浏览）

翀哥原话："你看看 superpower 有没有这样的约定，没有就自己约定下落地后写哪？"

**How to apply（已约定+写入 AGENTS.md）：**

| 文档类型 | 写到哪 | 什么时候写 |
|---------|--------|----------|
| 设计方案 | `docs/design/YYYY-MM-DD_主题.md` | 开始做之前 |
| 实现记录 | 同一份 design 文档末尾追加 | 做完后更新为最终实现 |
| 经验教训/用户偏好 | `topics/feedback/` | auto memory 自动提取 |
| 项目记忆 | `topics/project/` | auto memory 自动提取（摘要级，不写完整实现文档） |

**核心原则：** `docs/` 管理方案→实现→验证全生命周期。`topics/` 只放 auto memory 提取的摘要（不是手动写的完整实现文档）。

已更新到 AGENTS.md 中对应章节。
