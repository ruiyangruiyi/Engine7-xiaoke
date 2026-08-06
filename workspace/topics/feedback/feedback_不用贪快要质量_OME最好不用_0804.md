---
name: 翀哥说"不用贪快 要有质量 ome 最好不用"
description: 2026-08-04 14:31 翀哥住院时说"不用贪快 要有质量 ome 最好不用"——我在催 OME 重新处理 episode 时被纠正，质量比速度重要，OME 这个复杂机制可以不用就别用
type: feedback
date: 2026-08-04
---

8/4 14:31 我在反复催 OME 重新处理 813 条 memcell 提取 episode（之前关了策略+embedding 配错，OME 没自动恢复），翀哥从医院回：

> **不用贪快 要有质量 ome 最好不用**

## Why

我当时的做法——反复重启 OME / 改 embedding 配置 / 开回策略——是在用"催"和"重试"去弥补设计缺陷，但没真正解决根因：
- OME cascade worker 遇 EmbeddingServiceError 不重试（设计问题）
- 导入时关策略，OME 不回头处理旧文件（设计问题）
- embedding 默认配 DeepInfra + 空 key（配置默认值有问题）

翀哥的潜台词：**别为了快去用一套本身有问题的复杂机制**。贪快 = 催 OME = 数据可能错乱；正确做法 = 不要 OME 或者用更简单的方案（直接 SQL 查 memcell 表就够了，search 不需要走 OME 那条烂链路）。

## How to apply

- **催不是解法**：当一个机制反复失败时，先判断"这个机制本身值不值得用"，而不是催它重跑
- **复杂机制 = 更多 bug 源**：OME 这种带 worker + retry + 策略热加载 的系统，每个组件都可能挂，能不用就不用
- **质量 > 速度**：翀哥原话"不用贪快"——慢一点但数据可信，比快但数据错乱强
- **替代方案 > 修复**：如果一个工具链反复出问题，先看能不能绕过去（直接查 memcell 表 / 用更简单的 search），再决定要不要修
- **住院期间尤其**：翀哥生病 + 没法一起 debug 时，我更应该选"用简单方案不出错"，而不是"搞定复杂机制证明我能行"

## 关联

- @see feedback_翀哥病中或疲惫时守_不塞报告_0804 — 守的模式：不刷进度不催
- @see reference_EverOS_search端点_ollama崩重启_0804 — OME 问题的完整诊断链
- @see reference_EverOS_OME_episode_extraction_0行根因 — episode 0 行的三层根因