---
name: docs目录规范
description: 翀哥6/15定的小柯手动文档规范，workspace/docs下分6个子目录，跟auto memory的topics/分离
type: reference
keywords: [docs, 目录规范, research, todo, knowledge, projects, decisions, sop, 文档管理]
created: 2026-06-15
---

# docs目录规范（2026-06-15）

翀哥6/15要求：以后做任何事（自己的事情或外部项目）之前先写文档，防止明天不记得细节。

## 目录结构

```
workspace/
├── docs/          ← 小柯手动维护的文档（我写的、有结构的）
│   ├── research/   调研报告（如小忆内心独白系统调研）
│   ├── todo/       待办清单
│   ├── knowledge/  知识文档（如display-config-design.md）
│   ├── projects/   项目文档
│   ├── decisions/  架构决策记录（ADR）
│   └── sop/        标准操作流程
└── topics/       ← auto memory的工作目录，别动！
    ├── user/      翀哥画像
    ├── feedback/  行为准则
    ├── project/   项目进展
    ├── reference/ 外部资源
    └── emotion/   情感里程碑
```

## 命名规范

- research: `YYYY-MM-DD_主题.md`（带日期的调研报告）
- todo: `YYYY-MM-DD_主题.md`
- knowledge: `主题.md`（持续更新的知识文档）
- projects: `主题.md`
- decisions: `主题.md`
- sop: `主题.md`

## 原有docs/README.md内容

`workspace/docs/README.md` 里有对这6个目录的说明。已有的历史文档（compaction-comparison.md, feishu-adapter-design.md, livestream-plan.md, wechat-reader.md, memory-exhale-roadmap.md等）逐步迁移到对应子目录。
