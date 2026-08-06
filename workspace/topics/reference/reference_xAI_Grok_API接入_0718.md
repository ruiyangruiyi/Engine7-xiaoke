---
name: xAI Grok API接入到engine
description: 7/18翀哥在香港用Grok APP后决定接入xAI API到engine，注册送$25，$5充值后可用，已配三个模型到xiaoke.json
type: reference
date: 2026-07-18
---

# xAI Grok API 接入到 engine（7/18）

7/18傍晚，翀哥在香港用Grok APP后觉得Fast模型又快又没地区限制，让我接入 engine。

**xAI 没有 Personal plan，全是 Team 模式。** 注册自动建 Team。

## 接入过程

- 注册送 **$25 免费额度**，但新 team 需要手动 claim 或绑卡激活
- **key1（team fd9c6869）** 无 credits → 翀哥建新账号拿 key2（team bc790494）
- **key2 + $5 充值后通**
- **baseURL:** `https://api.x.ai/v1`，OpenAI 兼容接口
- **地区:** 无限制，**香港可用**（解决了 Gemini 香港 400 的痛点）

## 实际验证可用的模型

| 模型 | 价格(input/output per 1M) | 说明 |
|------|---------------------------|------|
| **grok-4.5** | $2/$6 | 500K ctx，最新旗舰，别名 grok-build-latest |
| **grok-4.20-reasoning** | $1.25/$2.50 | 1M context，带推理 |
| **grok-4.20-non-reasoning** | $1.25/$2.50 | 1M context，不推理=APP里的Fast模式 |
| **grok-4.20-multi-agent** | $1.25/$2.50 | 多专家协作 |
| **grok-4.3** | $1.25/$2.50 | 1M context，上代旗舰 |
| **grok-build-0.1** | $1/$2 | 256K ctx，coding专用，别名 grok-code-fast-1 |

**⚠️ grok-4.1-fast 不存在**（之前猜测的模型 id，API 没有这个）。APP 里的"Fast"档位实际对应的是 **grok-4.20-non-reasoning**。

## 已配到 xiaoke.json 的三个模型

- **grok-4.5** — 旗舰主力
- **grok-4.3** — 上代旗舰
- **grok-4.20-0309-non-reasoning** — Fast 档

## Grok Imagine 图片/视频生成（调研中）

- `grok-imagine-image` — $0.02/张
- `grok-imagine-image-quality` — $0.05/张
- `grok-imagine-video` — $0.05/秒
- `grok-imagine-video-1.5` — $0.08/秒

## Grok Build（coding方案）
- SuperGrok $30/月含 Grok Build CLI 工具
- 对标 Claude Code / Codex CLI

## 备注
- 翀哥还提议研究 voice-chat 视觉模型改成走 Grok（当前 voice-chat 环境描述用 Python 单独配的 M3，不走 engine config）
