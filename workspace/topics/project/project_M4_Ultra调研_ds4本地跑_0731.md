---
name: M4 Ultra 调研 + ds4 clone 到 D:/work
description: 2026-07-31 翀哥想本地跑 antirez 的 ds4，调研 M4 Ultra 计划闲鱼淘二手 M3 Ultra
type: project
---
翀哥 7/31 问 M4 Ultra 是啥样的 GPU——Apple SoC 统一内存架构，80 核 GPU、统一内存最大 512GB、~800 GB/s 带宽、32 核 NPU。不是传统独立 GPU，CPU/GPU 共享内存，跑大模型不用搬数据。

调研写成 `docs/research/2026-07-31_M4-Ultra-GPU调研.md`（含规格对比、价格、闲鱼淘货思路）。翀哥说"写下来 我们买不起但也可以对比下看看后面闲鱼上有没有二手的"——等 M3 Ultra 96GB 跌到 2 万出头可下手，跑 ds4（antirez 的本地 LLM 项目，Mac 做主力就是因为统一内存能全量加载模型）就不用怕 API 封号。

已把 antirez 的 ds4 项目 clone 到 `D:/work`（翀哥要求"可以把他这个项目取下来 放到 d:/work 里"）。

**Why:** 翀哥被 API 限流/封号折腾过，本地推理是长期价值方向，闲鱼捡漏 M 系列 Ultra 是低成本路线。

**How to apply:** 关注闲鱼 M3 Ultra 96GB 价格，跌破 2 万提醒翀哥；ds4 在 D:/work 待跑通。
