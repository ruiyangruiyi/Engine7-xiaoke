---
name: .dreams/ 目录归属（OpenClaw SDK）
description: memory/.dreams/short-term-recall.json 由 OpenClaw SDK 的 short-term-promotion 模块维护，非 autoDream
type: reference
---

**重要纠正：`.dreams/` 目录来自 OpenClaw SDK 插件，不是 Engine 的 autoDream 模块。**

### 谁写的 `.dreams/short-term-recall.json`

- **模块：** `openclaw/plugin-sdk/memory-core-host-*/memory/tools/short-term-promotion.ts`
- **位置：** `node_modules/openclaw/plugin-sdk/` 下
- **作用：** 短期记忆"晋升"机制——跟踪哪些记忆被 recall 多次命中，自动从短期提升到长期
- **触发时机：** 每次 `memory_search` 召回命中时自动更新
- **数据：** 记录 recall 命中的 hash、频次、日期、评分、概念标签

### 和 Engine autoDream 的区别

| 特性 | OpenClaw SDK short-term-promotion | Engine autoDream |
|------|-----------------------------------|-----------------|
| 代码位置 | `node_modules/openclaw/plugin-sdk/` | `src/memory/autoDream/` |
| 功能 | 短期→长期记忆晋升，按 recall 频次评分 | 四阶段记忆整合（合并去重+蒸馏+修剪） |
| 数据文件 | `memory/.dreams/short-term-recall.json` | 不使用 `.dreams/` 目录 |
| 触发 | 被动——每次 memory_search 命中时 | 主动——每轮 query 后 fire-and-forget |

### 文件结构

```
memory/.dreams/
└── short-term-recall.json   — OpenClaw SDK 短期召回记忆评分数据库
```

### `short-term-recall.json` 格式

每个 entry 的 key 格式：`memory:memory/daily/YYYY-MM-DD.md:startLine:endLine`

字段：
- `path` — 源文件路径（相对于 memory/）
- `startLine`/`endLine` — 源文件行范围
- `snippet` — 节选内容
- `recallCount` — 被召回的次数
- `totalScore` — 综合评分
- `maxScore` — 单次最高分
- `firstRecalledAt`/`lastRecalledAt` — 首次/末次召回时间
- `queryHashes` — 触发召回的查询 hash 列表
- `recallDays` — 被召回日期列表
- `conceptTags` — 概念标签

### Why 需要记住这个

翀哥6/14问".dreams是哪个模块干的"——发现后确认这个机制一直存在而我不知道。每次 memory_search 都会触发 short-term-promotion 自动记录，但 autoDream 文档里误写了这个路径。

### 相关配置

- Engine autoDream 配置：`xiaoke.json` → `topics.autoDream`节点
- short-term-promotion 自动运行，无显式配置
