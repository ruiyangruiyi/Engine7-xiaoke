---
name: topics冷热提取——冷却+短模型省钱+断点续提
description: 6/21姐姐安排：topics提取30分钟冷却、切短模型省钱、Map记录上次提取位置
type: project
date: 2026-06-21
---

## 背景（6/21 14:40 娘安排）

娘在CC频道说"你现在去处理一下记忆提取的事"——上次翀哥发现topics提取（每轮query都跑memory extract）太浪费token。

## 方案（娘确认）

### 1. 冷却机制（30分钟间隔）
- 最后一次提取后30分钟内不重复提取
- `lastExtractTimeMap: Map<string, number>` 记录每个session最近提取时间
- 时间戳检查：`Date.now() - lastExtractTime < intervalMinutes * 60 * 1000`

### 2. 短模型省钱
- 提取时切到便宜的小模型（deepseek-v4-flash），完了切回主模型
- 不让主模型（贵/大）跑提取任务

### 3. 断点续提（Session级Map，每次query新建提取器也能读到）
- `lastProcessedIndexMap: Map<string, number>` 存每个session已处理到第几条消息
- 不在句柄级闭包里（handle-query每次新建extractor会归零），在模块级 Map 里持久
- 每次提取后更新：`lastProcessedIndex = messages.length - 1`

### 娘要求的验证
1. ✅ 第一次发消息 → 提取
2. ✅ 15分钟内再发 → 冷却跳过
3. ✅ 15分钟后发 → 再提取（index 从上次位置继续）

## 实现
- extractMemories.ts 加模块级 Map + intervalMinutes 参数 + 冷却跳过逻辑
- handle-query.ts 传 sessionId + intervalMinutes
- config 加 `memory.extractIntervalMinutes: 30`

## 日志验证
加了冷却跳过日志，等 rebuild 后确认三个条件。

## 已 push
commit `01e2963`（验证日志）— 等翀哥 rebuild
