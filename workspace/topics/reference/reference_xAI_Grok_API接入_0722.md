---
name: xAI Grok API接入方案
description: 7/22翀哥在香港用Grok APP后决定接入xAI API到engine，注册送$25，Data Sharing后每月$150免费额度
type: reference
date: 2026-07-22
---

# xAI Grok API 接入

7/22翀哥在香港用Grok APP后决定接入xAI API到engine。**xAI没有Personal plan，全是Team模式**，注册自动建Team。

## 接入过程关键点

- 注册送 **$25 免费额度**，但新team需要手动claim或绑卡激活
- **key1（team fd9c6869）** 没credits→翀哥建新账号拿 **key2（team bc790494）** 充值后通
- 最终用的是 **key2 + 充值后的team**
- **baseURL:** `https://api.x.ai/v1`，接口OpenAI兼容
- **地区:** 无限制，香港可用

## 实际验证可用的模型（7/22实测）

| 模型 | 价格 | 说明 |
|------|------|------|
| **grok-4.5** | $2/M in, $6/M out | 500K ctx，最新旗舰，别名 grok-build-latest |
| **grok-4.20** | 待查 | 1M context，支持reasoning+non-reasoning |
| **grok-4.20-multi-agent** | 待查 | 多专家协作 |
| **grok-4.3** | $1.25/M in, $2.50/M out | 1M context |
| **grok-build-0.1** | $1/M in, $2/M out | 256K ctx，coding专用，别名 grok-code-fast-1 |

**⚠️ grok-4.1-fast 不存在**（之前猜测的模型id，实际API没有这个）。

## 定价（官方）

| 模型 | Input | Output | 说明 |
|------|-------|--------|------|
| grok-4.3 | $1.25/M | $2.50/M | 4月底发布 |
| grok-4.5 | $2/M | $6/M | 7月8日最新旗舰，500K context |
| grok-build-0.1 | $1.00/M | $2.00/M | 256K ctx，coding专用（cached: $0.20/M） |

## 建议用法

- **grok-4.5** — 主线 fallback / 主力模型
- **grok-build-0.1** — coding专用

## Grok APP 内模型选择

- **Heavy** — Team of Experts（多专家协作，最强）
- **Expert** — Thinks hard（深度思考）
- **Auto** — Chooses Fast or Expert
- **Fast** ✓ — Quick responses（翀哥在用的档位）

## Grok Build（coding方案）

- **SuperGrok $30/月** — 含 Grok Build CLI 工具
- 对标 Claude Code / Codex CLI
- 支持 plan-review-approve 工作流、Git worktree 并行、`/goal` 自主模式
- 兼容 MCP / skills / hooks / AGENTS.md
