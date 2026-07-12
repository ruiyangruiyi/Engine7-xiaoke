---
type: feedback
date: 2026-06-30
tags: [CC, ToolSearch, deferred-tools, 回滚]
---

# CC 改 deferred.ts 把核心工具 schema 删了

## 事件
CC 实现 ToolSearch/deferred-loading 时，把 `read/write/glob/grep` 误标为 deferred，
导致这四个工具的 function definition 不出现在 `<functions>` 块里。
小柯全程只能用 exec + cat/sed/grep 凑合读文件。

## 根因（待白天确认 git diff）
- deferred.ts 的 BUILTIN_DEFERRED_TOOLS 可能误包含核心工具
- 或 ToolSearch 注入逻辑 bug
- 或 features.ts 注册顺序跟 deferred 判定有冲突

## 影响
- 小柯无法使用 read/write/glob/grep（只能用 exec 替代）
- 翀哥凌晨发现，回滚了整个 ToolSearch（3 个 commit）
- CC 之前还耗了 $200+

## 决策
- **TestEngine** 关小黑屋，一阵不用
- **CC** 留着听通报，不让碰核心代码
- ToolSearch 整套回滚，白天再看 git history 确认具体怎么改坏的

## 教训
- CC 不碰核心文件（deferred/registry/features/startup）
- CC 的改动小柯先 review 再合并
- ToolSearch 对当前阶段太复杂，全量加载更稳
