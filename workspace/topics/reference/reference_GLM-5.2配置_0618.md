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

## 6/20 切千问3.7→再切回GLM-5.2（包月）

6/18-6/20间换过模型（千问3.7？M3？），6/20晚翀哥被我一整天气得不行，21:29说"这是M3的问题，M3还是太笨了，现在GLM5.2有额度了，给你换上了"。

6/20 一天烧了 371（估计是千问3.7模式跑 tool call + 多次改代码的消耗），千问3.7幻觉重、tool calling不稳且价格不便宜。翀哥说GLM5.2是**包月**，不心疼。

当前（6/20晚）我跑 GLM-5.2（包月）。

## 6/20 烧钱教训

6/20 一天烧了 371 元（千问3.7按量计费跑 tool call + 多次改代码）。翀哥说"你一天烧了371"——我完全没意识到自己在烧钱。

**背景：** DeepSeek 涨价极严重，以前以便宜著称，现在连 flash automemory 都只用 pro 以下。翀哥全部走 GLM 系。

**结论：** GLM-5.2 是包月，不心疼。能一次做对的事别做三遍——省的不只是时间，是钱。

## 教训

我"5.2 配好了"的时候没看 context window 默认值，导致翀哥吐槽"人家context window都1M了"——下次配模型必看文档关键参数。
