---
name: Anthropic Provider 伪装成 CC 请求格式
description: 2026-07-29 所有 anthropic provider 写死完整 CC header（含 X-Stainless 全家桶 + anthropic-beta），authMode/apiVersion/headers 配置字段全部删除
type: reference
created: 2026-07-29
date: 2026-07-29
---

2026-07-29 翀哥要求所有 anthropic provider（minimax、zai-anthropic、deepseek、dashscope-tp）**伪装成 CC 的请求格式**。

## CC 完整 Header 格式（最终版）

```http
Content-Type: application/json
anthropic-version: 2023-06-01
Authorization: Bearer <token>
User-Agent: claude-cli/2.1.220 (external, cli)
x-app: cli
X-Claude-Code-Session-Id: <uuid>
# X-Stainless 全家桶（SDK 0.94.0 指纹）
x-stainless-arch: arm64
x-stainless-lang: js
x-stainless-os: Windows
x-stainless-package-version: 0.94.0
x-stainless-runtime: node
x-stainless-runtime-version: 22.14.0
x-stainless-sdk: js
# 特性开关
anthropic-beta: claude-code-20250219, message-errors-20250506, max-tokens-3.5-sonnet-2024-07-15, output-128k-2025-02-19, prompt-caching-2025-02-19, computer-use-2025-01-24
```

## 来源

翀哥 2026-07-29 13:26 从本地安装的 CC 2.1.220 二进制中逆向扒出：

1. **第一层 — lib/shared/common.ts**: `getHeaders()` — UA + x-app + X-Stainless 全家桶 + authorization 构造
2. **第二层 — hro() 函数**: 额外追加的 header（session-id 等）
3. **第三层 — auth 相关**: Bearer token + anthropic-beta 特性开关

## 实现方式

- **anthropic-provider.ts** 写死完整 CC header，所有 anthropic provider 统一走此格式
- UA 版本号 `2.1.220`（跟 CC 最新版同步）
- 日志前缀 `🔒` 放在 `→` 前面，一眼看出请求前已设置
- 不加 `authMode`、`apiVersion`、`headers` 等配置字段到 loader/provider-factory/xiaoke.json
- token-plan(dashscope) 也走 Bearer，跟 CC 一致

## 关键决策

翀哥原话：
1. "默认就是Bearer哦 我感觉删了也行 就不配了 简单 就直接anthropic格式"
2. "都删了吧 都用CC的格式 不配了 本来也应该是这样"
3. "不是不是 都伪装成CC" — 不只是 auth，而是完整 CC header
4. "默认就是CC的对吧  之前的都删了" ✅（最终确认）
