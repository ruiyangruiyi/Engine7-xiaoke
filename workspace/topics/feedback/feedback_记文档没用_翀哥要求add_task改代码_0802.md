---
name: 记文档没用——翀哥要求 add-task 改代码
description: 8/2 翀哥纠正"你这么记有什么意义呢，让你记肯定你要 add task 的"——发现可优化点必须落到 calendar 任务，光写 docs 不动代码等于没记
type: feedback
---
2026-08-02 16:34 翀哥纠正我：发现 Engine provider 模型列表不能热加载后，我写了 `docs/knowledge/Engine-热加载边界.md` 总结规则。翀哥立刻批评："**你这么记有什么意义呢，让你记肯定你要 add task 的**"。

**Why:** 写文档是"事后总结"，add-task 才是"未来会改"——翀哥要的不是知识沉淀，是排进 calendar 等做的真实工作。文档只在 add-task 没法做时才有用（比如纯方法论、纯踩坑笔记）。

**How to apply:**
- 发现任何**代码层/系统层**的可优化点 → 立即 `add_task` 加进 calendar（带 doc_path 关联到对应文档），不要只写 docs 就完事
- 文档的角色是**任务的背景说明**（给未来的我看为什么这么做），不是终点
- 纯方法论/纯踩坑（没法落地成代码改动）→ 才写 docs
- 写完 docs 顺手 `add_task` 不算错（文档+任务配套），只写 docs 不 add_task = 没记