---
name: OpenClaw Engine Architecture
description: 自研引擎（engine/）TypeScript源码架构、已知问题、Phase规划
type: reference
keywords: [engine, typescript, provider, tool, query, streaming, 架构]
created: 2026-05-27
updated: 2026-05-27
---

## 位置

`C:\Users\24045\.openclaw\engine\` — 自研AI agent引擎，取代OpenClaw gateway核心。

## 技术栈

- TypeScript 6.x, ESM (`"type": "module"`), Node >=22
- tsconfig: ES2024 / Node16 module resolution, strict mode
- 零运行时依赖（只有 @types/node + typescript devDep）

## 架构分层

```
main.ts (REPL入口)
  └→ QueryEngine (core/query.ts) — async generator agent loop
       ├→ LLMProvider (models/provider.ts 接口)
       │    ├→ OpenAIProvider (models/openai-provider.ts) — GLM/DeepSeek/Qwen/Ollama
       │    └→ AnthropicProvider (models/anthropic-provider.ts) — Claude/MiniMax
       ├→ ToolRegistry (tools/registry.ts) — Hermes风格自注册单例
       ├→ ToolExecutor (tools/executor.ts) — tool_call → handler → tool_result
       └→ FeatureResolver (tools/features.ts) — 按profile开关决定加载哪些tool
```

## 关键类/接口

| 类/文件 | 职责 |
|---------|------|
| `QueryEngine` | async generator + while(true) 循环，AbortController支持打断，maxLoops=10 |
| `LLMProvider` 接口 | `streamChat()` + `formatMessages()` + 可选 `chat()` |
| `OpenAIProvider` | OpenAI兼容SSE streaming，system放messages首位 |
| `AnthropicProvider` | SSE event类型解析(content_block_start/delta/stop)，system单独传 |
| `ToolRegistry` (单例) | `register() / get() / list() / definitions()` |
| `Tool` 接口 | name/description/schema/handler + 可选 isConcurrencySafe/isReadOnly/isDestructive |
| `StreamChunk` | type=text/tool_call/tool_result/thinking/done/error |
| `Message` | OpenAI兼容格式(role/content/tool_calls/tool_call_id) |

## 内置工具

| Tool | 文件 | 状态 |
|------|------|------|
| `memory_search` | tools/memory-search.ts | 可用，关键词匹配搜memory/ + topics/ |
| `msg_send` | tools/msg-send.ts | stub，Phase 3接真实Channel |

## 配置

`openclaw.json` 在 engine 根目录。`loadConfig()` 支持环境变量覆盖：
- `ENGINE_CONFIG` — 配置文件路径
- `ENGINE_MODEL` — 模型引用 (provider/model格式)
- `ENGINE_WORKSPACE` — workspace路径
- `ENGINE_AGENT` — agent ID

## Phase规划（来自架构图）

- ✅ Phase 0-2: 核心引擎 + Provider + Tools (~1200行TS)
- ⏳ Phase 3: Channel通道 (Discord/微信/飞书 Adapter + BasePlatformAdapter)
- ⏳ Phase 4-5: Session Manager (JSONL持久化) + Memory Store + Heartbeat/Cron
- ⏳ Phase 6+: 多Agent路由

## Code Review发现的已知问题 (5/27)

### 🔴 严重

1. **`features.ts:21` 用 `require()` 在ESM环境会炸** — setup()用CommonJS require但package.json是ESM module。且setup()从未被调用（死代码）。
2. **`openclaw.json` 明文API key** — zai/zai2/tavily的key全部明文，无环境变量覆盖机制。

### 🟡 中等

3. **`api.ts` 和 `openai-provider.ts` SSE解析完全重复** — 同样的buffer管理、tool call累积、[DONE]处理逻辑复制了两份。api.ts是早期版本，provider抽象后应该删掉或内部委托。
4. **`StreamChunk` 定义重复三处** — api.ts、provider.ts各定义一份，应该统一到provider.ts。
5. **`main.ts` REPL不记录tool交互到conversationHistory** — 只存最终文字，tool调用/结果全丢失。下一轮对话LLM看不到之前的tool历史。
6. **`openclaw.json` 的 `api` 字段跟代码不匹配** — minimax-cp配置 `"api": "anthropic-messages"` 但 loader.ts/factory.ts 只认 `'openai-completions' | 'anthropic'`，会走到default报错。

### 🟠 建议改进

7. **`anthropic-provider.ts:53` JSON.parse无try-catch** — LLM返回非法JSON会throw整个provider。
8. **`executeTools` 串行执行** — Tool接口有 `isConcurrencySafe()` 但没用到，多tool call应该并行安全tool。
9. **`loadConfig` 不验证workspace存在** — 路径错误时memory_search静默返回空。
10. **`memory-search.ts` 纯文本匹配** — 配了ollama bge-m3但没用上（Phase 4-5计划）。
