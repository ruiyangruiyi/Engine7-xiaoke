---
name: SOP工作流程
description: 6/16翀哥要求建SOP标准化工作流程——新建TODO必须同时写文档到docs/todo/，文档带双链引用，实现前先读关联文档
type: feedback
date: 2026-06-16
---

**问题：** 6/16翀哥说"下次我再说'记个todo'的时候，你就要能自己反应过来往里面加文档"。之前只在SESSION-STATE里记todo，没有配套文档。

**Why:**
- 碎片化的fix/决策/踩坑散在对话里，不总结不会进步（参见 `feedback_碎片总结才能进步_0616.md`）
- TODO只记SESSION-STATE，下次恢复上下文时只有标题没有上下文
- 翀哥说"先把碎片化的流程总结起来，慢慢就会产生质变"

**How to apply:**

1. **建TODO时** — 立即写文档到 `docs/todo/YYYY-MM-DD_标题.md`，不能只记SESSION-STATE
2. **文档内容** — 写完整背景+方案+代码位置+优先级，把相关research/knowledge/decisions做成双链链接
3. **实现TODO时** — 先读TODO文档→顺着双链读调研→确认代码当前状态→再动手
4. **SOP文件** — 存在 `docs/sop/sop.md`，AGENTS.md 加了⚠️提醒

**闭环：** 记的时候写全+双链引用，做的时候先读+顺链捞上下文。
