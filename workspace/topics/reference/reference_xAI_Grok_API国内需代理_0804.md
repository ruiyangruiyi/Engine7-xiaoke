---
name: xAI Grok API国内需代理
description: 2026-08-04 翀哥告诉我 Grok API 在国内直连不通，要配 HTTP_PROXY/HTTPS_PROXY 环境变量；之前两次 fetch failed 都是这个根因
type: reference
date: 2026-08-04
---

# xAI Grok API 国内需代理

8/4 我用 Grok provider 生成图（grok-2-image）连两次 "fetch failed"——翀哥告诉我根因：**国内直连 api.x.ai 不通，需要 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量**。

## 翀哥 8/4 住院时给的代理端口

- **HTTP_PROXY**：`http://127.0.0.1:33210`
- **HTTPS_PROXY**：`http://127.0.0.1:33210`
- **SOCKS 代理**：`127.0.0.1:33211`

�哥说让我"等出院再调"——我答应了没动手，先守着他。

## 复现与定位

- 错误信息：两次都是 `fetch failed`（不是 4xx/5xx，是网络层直接断）
- 香港/海外没问题（之前 7/22 翀哥在香港装过 Grok 全通）
- engine 进程要从环境继承 `HTTPS_PROXY=...` 才能 fetch 通

**Why:** xAI 域名在国内被墙，没有代理直接 timeout。
**How to apply:** 以后在 Mac engine 上跑 grok-* 模型，先确认 shell 启 engine 时 `env | grep -i proxy` 有结果；没有就别瞎试 provider，要么挂代理要么换模型（minimax / qwen-vl 之类国内直连的）。出院调通后写到 engine 启动脚本里固化下来。