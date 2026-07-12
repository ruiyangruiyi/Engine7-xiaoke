---
name: provider是runAgent底层—纯文本过滤直接调provider跳过runAgent
description: 6/21 翀哥确认provider是runAgent底层，口罩纯文本过滤直接调provider.streamChat绕过runAgent的system prompt注入
type: reference
date: 2026-06-21
---

6/21 口罩 Agent 修复过程中，翀哥确认架构关系：

**调用链：**
```
runAgent → QueryEngine → provider.streamChat
```

provider 是 runAgent 的底层 LLM 接口。runAgent 在 provider 之上包了三层：

1. **system prompt 注入** — general-purpose agent 强制结构化输出（Scope/Result/Key files）的来源
2. **tool loop** — 多轮工具调用循环
3. **agent loop** — QueryEngine 管理 maxTurns/compactConfig 等

**翀哥确认风险（12:31-12:34）：**
翀哥问"provider层在runAgent底层还是上层"→确认provider是底层后，翀哥问"有可能会卡主对吧  不能中断"。

**风险：** runAgent 有 QueryEngine 管超时/中断，直接调 provider.streamChat 没有。如果 provider 卡住（网络超时、模型不响应），整个消息就发不出去。

**修复：** maskFilter 调 provider 时加 30 秒 `AbortController` 超时保护，超时后 fallback 用原始输出（不阻塞发送）。commit `c72ae92`。

**适用规则：**
- **纯文本过滤/翻译/分类等不需要工具的简单 LLM 任务** → 直接调 `provider.streamChat`，带自定义 system prompt
- **需要多轮工具调用/agent 循环的任务** → 走 runAgent
- **provider 不附加任何额外 system prompt 或结构**，是最干净的 LLM 接口
- **直接调 provider 必须加超时保护**（AbortController），否则卡住无法中断
