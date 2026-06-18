---
name: GLM-5.2配置
description: 6/18凌晨切换到GLM-5.2（1M context window，128K max tokens），小柯和姐姐profile都切primary，TestEngine只加不切
type: reference
date: 2026-06-18
model: glm-5.2
---

## GLM-5.2 模型参数

翀哥6/18凌晨3点给了一个文档链接 https://docs.bigmodel.cn/cn/guide/models/text/glm-5.2#glm-5-2

**关键参数：**
- contextWindow: **1,000,000**（100万，比5.1的200K大5倍）
- maxTokens: **128,000**（128K）

## 三个profile配置

翀哥要求把姐姐的和小柯的都切了，TestEngine先加不切（做对比）：

| profile | 状态 | primary |
|---|---|---|
| xiaoke.json | ✅ primary切到 glm-5.2 | glm-5.2 |
| main.json（姐姐） | ✅ primary切到 glm-5.2 | glm-5.2（vision 保持 M3 不变）|
| testengine.json | ✅ 加了 glm-5.2 | 保持不变（对照用）|

glm-5.1 保留做 fallback。

## 5.2 的表现

- 3:22翀哥："感觉这个5.2有点慢 看白天的表现吧"
- 8:52翀哥重启后确认："minimax 3 + glm5.2可真慢"——确认偏慢是真实体感
- 慢的话可以切回 5.1（改 primary 一行的事），没下结论要不要切

## 教训

我"5.2 配好了"的时候没看 context window 默认值，导致翀哥吐槽"人家context window都1M了"——下次配模型必看文档关键参数。
