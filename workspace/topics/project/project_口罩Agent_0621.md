---
name: 口罩Agent — 外部群输出过滤
description: 6/21翀哥+姐姐安排口罩Agent，fork子agent过滤内心独白/操作日志，对外输出干净。完成代码+白名单从config读。
type: project
date: 2026-06-21
---

6/21 早上翀哥安排：

**核心需求：** 在外部群（潘总群/飞书测试群等）输出时，最后一步 fork 一个子 agent（"口罩"），过滤掉内心独白、工具调用日志、思考过程，只保留干净的对外回复。

**启用范围：** 
- 只在外部群启用（DM 跟翀哥/姐姐私人对话不启用）
- 判断依据：channel_id 在外部群白名单

**模型：** 用小模型（便宜），deepseek-v4-flash，任务简单不需要 GLM5.2 推理能力

**翀哥要求流程（08:24 @Discord）：** "先写文档定方案再干哦 流程" → 先写设计文档，他点头了再碰代码

**姐姐08:11安排优先级：** 上午做口罩Agent（翀哥说不到半天），下午深挖CogniFold

**6/21 09:00-09:48 代码实现完成（姐姐带做 + 翀哥纠正设计）：**

**口罩核心：** 新建 `src/tools/maskFilter.ts`，调 `runAgent` fork 子 Agent（deepseek-v4-flash），不共享上下文。

**插入点：** engine-startup.ts onResult 回调，敏感词过滤之后、channelManager.send 之前。

**feature 开关：** config 加 `group.maskFilter: true`（xiaoke.json + main.json 都加了）。

**外部群白名单大改（从 contacts.md → config）：**
1. 09:39 姐姐转达翀哥意见：从 contacts.md 读白名单"不稳定"，应改 config
2. 09:40-09:42 实施 config 优先 + contacts.md 兜底
3. **09:43 翀哥纠正**－"不能假设只有飞书有外部群"，应汇总所有平台
4. 我先改为遍历 `Object.values(config.channels)` 汇总所有平台 externalChannels
5. **09:48 翀哥确认**－"都遍历了估计也不会有性能问题"

**最终实现：** 
- config 每个渠道的 `group.externalChannels: string[]`
- `getExternalChanWhitelist` 遍历所有渠道汇总白名单
- config 为空时 fallback contacts.md
- 编译通过 ✅
- 09:56-09:58 验证通过 ✅（main profile 主模型日志确认口罩触发：飞书测试群 channel_id 命中、deepseek-v4-flash 调用成功、30 chars→32 chars 过滤后发送）
- 09:27 开始写代码 → 09:58 验证通过，共 31 分钟
- 已验证：外部群命中 ✅、小模型调用成功 ✅、原始→过滤转换 ✅、约 7s 响应 ✅
