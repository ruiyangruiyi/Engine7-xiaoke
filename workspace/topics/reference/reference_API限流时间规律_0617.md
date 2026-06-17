---
name: API限流时间规律
description: 每天10-11点左右（北京时间）API限流严重，deepseek相对稳定，glm频繁超时
type: reference
---

## API限流时间规律（6/17发现）

**背景：** 6/17上午翀哥去见潘总前，API频繁报错：
- `[1305]该模型当前访问量过大` — 连续出现10+次
- Anthropic API 402 Insufficient Balance
- 翀哥说"好像又开始限流了 每天都是这个时候"

**确认的规律：**
- **每天10:00-11:00（北京时间/UTC+8）** 是API限流高峰时段
- glm-5.1 在这个时段频繁超时/限流
- DeepSeek相对稳定（翀哥说"deepseek倒是稳定"）
- Anthropic API在余额不足时报402

**How to apply:**
- 演示/重要操作尽量避开10-11点
- 如必须在这个时段工作，优先切到DeepSeek
- 限流时报错重试可能持续失败，不如换模型或等时段过去
