# preview→onResult 延迟修复（2026-08-05 翀哥反馈）

## 现象

翀哥 8/5 上午反馈："每次预览能看到出了 很长时间才会 onResult"，"换到 dsflash 了还是卡"。

## 日志实锤

- 09:10:10 feishu:send 308 chars（preview 预览，流式实时推）→ 09:13:12 onResult 892 chars（最终消息）——**中间隔 3 分钟**
- 09:11:31 翀哥发 /ps → 09:24:53 才被作为 steer 注入——**queue 卡了 13 分钟**
- 09:14:48 memory-extract finished in 729440ms（12 分钟！MiniMax 429 重试风暴）

## 根因

**preview（预览）和 onResult（最终消息）不是同一个时机：**
1. preview = 流式输出实时推给飞书（用户立刻看到）
2. onResult = 整轮 query 完全结束才发最终消息——**如果这轮 query 里有 tool call（exec/read/查日志），onResult 必须等所有 tool 完成 + LLM 重新总结**

所以"预览出了很久才 onResult" = **agent 在用 tool 干活，正式回复等干完才发**。不是 provider 卡（deepseek 活着且快）。

**次要因素**：memory-extract 每 15 分钟跑一次，用 MiniMax 429 重试每次 12 分钟，可能挤占队列资源。

## 短期对策（立即生效）

- 回复翀哥消息不用 tool，直接说——预览即最终，不卡
- 长任务（查日志/修 bug）查完一次性回，中间不占 queue

## 机制修复（出院后做）

**preview 完成后直接 freeze 为最终消息**，不等 onResult 的 tool call——参考 6/18 preview freeze 机制（replyTo 关联最终消息 + 卡片不删）。

具体改法待定：
- 方案 A：preview 流结束即交付（freeze），onResult 只做补充（如 tool 后的最终结果）
- 方案 B：减少 query 内的 tool call（回复优先，tool 后置）
- 方案 C：memory-extract 失败快速降级（429 时跳过或缩短重试），不占 12 分钟

## 状态

- [ ] 8/7 14:00 启动修复
- [ ] 短期待办：回复不用 tool（已开始执行）
