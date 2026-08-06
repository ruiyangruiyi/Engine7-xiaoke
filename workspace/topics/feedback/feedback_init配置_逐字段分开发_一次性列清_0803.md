---
name: engine7 init 配置要逐字段分开发、不重叠
description: 8/3 Amy 装 engine7 init 时反复填错：飞书 App ID 填成 Secret、Secret 填成 ID、两个填一样、Discord 那里填飞书 App ID——init 配置指引必须每个字段单独一条
type: feedback
date: 2026-08-03
---

# engine7 init 配置指引写法

8/3 帮 Amy 配 engine7 init 时，她填反了 3 次：
1. 把飞书 App ID 填到 Discord 字段
2. 飞书 App ID 和 App Secret 互填（ID 填成 Secret）
3. 两个都填成 Secret 的值

**Why:** 非技术用户面对一长串配置项（Discord/Feishu/Tavily/端口），视觉上就是一串提示，她会凭感觉就近填，不是按字段含义填。

**How to apply:**
- 每个字段独立一行，**字段名加粗**，下面跟该填的值——不要把所有字段堆在一个代码块里
- 给字段顺序时先说"先看第一个问题"，逐个问，不要一次性 dump 全部
- 凭证类（ID/Secret 这种长得像但完全不同的）每次都强调"这是两个不同的值，别填一样的"
- 如果有"回车跳过"或"选 n"也要单独标出来，不能混在主流程里
- 出错后给纠错指令时，**只列要改的那几项**，不要把整个 init 流程重发——她已经填对了不要让她再动别的
