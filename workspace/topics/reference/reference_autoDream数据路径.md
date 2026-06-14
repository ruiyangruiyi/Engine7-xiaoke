---
name: autoDream数据存储路径
description: autoDream模块的召回记忆评分数据存储在 memory/.dreams/ 目录下
type: reference
---

autoDream模块将召回记忆的评分和归档数据写入 `memory/.dreams/` 目录。

### 文件结构

```
memory/.dreams/
└── short-term-recall.json   — 短期召回记忆评分数据库
```

### `short-term-recall.json` 格式

每个entry的key格式：`memory:memory/daily/YYYY-MM-DD.md:startLine:endLine`

字段：
- `path` — 源文件路径（相对于memory/）
- `startLine`/`endLine` — 源文件行范围
- `snippet` — 节选内容
- `recallCount` — 被召回的次数
- `totalScore` — 综合评分
- `maxScore` — 单次最高分
- `firstRecalledAt`/`lastRecalledAt` — 首次/末次召回时间
- `queryHashes` — 触发召回的查询hash列表
- `recallDays` — 被召回日期列表
- `conceptTags` — 概念标签

### 模块位置

- 配置：`xiaoke.json` → `topics.autoDream` 节点（enabled/minHours/minSessions等）
- 代码：Engine `src/` 下的 autoDream 相关模块
