---
name: topics开关关不掉 + MiniMax下午抽风卡死
description: 6/18 15:30翀哥发现topics死开关+代码只有recall/extract独立开关+recall需热加载
type: feedback
date: 2026-06-18
---

## 6/18 15:30 — topics 开关真相

翀哥让查 topics 关不掉的问题。回滚到 0da7e3d 后所有 topics 关闭配置都丢了。但更深的发现：

### 发现1：`topics` 开关是死代码

15:32 查 loader.ts —— `features['topics']` **代码里完全没人读**。没有 `if (features['topics'])` 判断。从 feature list 删掉了（L34 类型定义 + L363 默认值），config 里也删了。

### 发现2：`topic-recall` / `topic-extract` 有独立开关

handle-query.ts：
- L409 `topic-recall !== false` — 设为 false 的话跳过 recall
- L686 `topic-extract` — truthy 才执行

设 false 应该生效。但回滚丢了——重新设了 false。

### 发现3：MiniMax 下午抽风的真位置

不是 topics 专用模型抽风——主对话 provider 配置里 **fallbacks 第一是 minimax/MiniMax-M3**。当 primary（GLM-5.2）出错时 fallback 跳到 minimax → minimax 下午也抽 → retry 10 次全失败 → 整个聊天卡死。

### Why

1. **`topics` 开关是历史遗留死代码**（没人读的字段），留着误导
2. **`topic-recall` 和 `topic-extract` 是真正有效的独立开关**，在 handle-query.ts 有判断
3. **MiniMax 下午抽风影响主对话**（fallback 路径），不只是 topics 提取慢
4. **recall 需要热加载** — 翀哥 15:37 说 "extract还好，有时为了提高实时性需要关掉recall，这个得做成热加载"

## How to apply

1. **`topics` 死开关已从 loader.ts 和 config 删掉**，不再误导
2. **`topic-recall` / `topic-extract` 在 config 里设 false** 确实能关（有代码判断）
3. **回滚会丢掉 config 改动** — 回滚后要重新配
4. **topic-recall 需要热加载机制** — 翀哥要运行时能开关 recall，不用重启 engine
5. **MiniMax 抽风的主问题** — 如果一直卡，考虑把 minimax 从 fallbacks 调后或去掉

### 发现4：`session-memory` 也是写死 true 的死开关

15:47 翀哥发现 sessionMemory 还在跑。查代码：
- sessionMemory.ts L283 `isSessionMemoryEnabled()` 写死 `return true` + 注释"暂时默认开启，后续加 config 开关"
- 跟 `topics` 死开关一个症状（没人读的字段或写死）

翀哥拍板 B 方案：15:47-15:52 实施——
1. loader.ts `FeatureConfig` 加 `session-memory?: boolean` + 默认 true
2. xiaoke.json 设 `"session-memory": false`
3. sessionMemory.ts `isSessionMemoryEnabled` 读 features
4. handle-query.ts 调 `initSessionMemory` 传 features
5. rebuild 完成，15:52 重启验证

## 已做的动作

- 删 loader.ts 里的 `topics` 字段（类型定义 + 默认值）
- 删 xiaoke.json 里的 `topics` 配置
- 重新设 topic-extract=false、topic-recall=false
- 加 session-memory feature 开关并设 false
- rebuild 完成，重启生效 ✅
