---
title: Streaming Event体系 vs cc-connect Review
date: 2026-05-28
reviewer: 张小柯
---

# Streaming Event体系 vs cc-connect 对比Review

## 对照源码

| 组件 | 文件 |
|------|------|
| Engine StreamChunk | `src/models/provider.ts` |
| Engine QueryEngine | `src/core/query.ts` |
| Engine Discord handler | `src/main.ts` L621-661 |
| cc-connect Event类型 | `core/message.go` L160-207 |
| cc-connect processInteractiveEvents | `core/engine.go` L3379+ |

## Event类型映射（✅ 对齐正确）

| cc-connect Event | Engine StreamChunk | Discord handler行为 |
|------------------|-------------------|-------------------|
| EventText | `type:'text'` | ✅ 只typing不发消息 (L631-634) |
| EventToolUse | `type:'tool_call'` | ✅ 🔧工具指示器 (L635-643) |
| EventToolResult | `type:'tool_result'` | ✅ 📤工具结果 (L645-650) |
| EventResult | `type:'result'` | ✅ 最终回答统一发Discord (L653-660) |
| EventThinking | `type:'thinking'` | ✅ 打印💭 |
| EventError | `type:'error'` | ✅ 错误reaction |
| EventPermissionRequest | — | ❌ 缺失 |

## 发现的6个问题

### 1. 🔴 EventText中间文字完全丢弃
- `onText: (_text) => {}` 忽略所有中间文字
- cc-connect做streaming preview（L3828-3896），实时显示LLM输出
- 多轮tool call时用户只看到🔧📤看不到LLM在"想什么"
- **优先级：高**

### 2. 缺EventPermissionRequest
- cc-connect有完整的permission流程（L3898-3975）
- Event类型定义里有但Engine未实现
- **优先级：低（以后sandbox/权限需要时补）**

### 3. 空result无提示
- maxLoops截断时finalText可能为空
- cc-connect处理：`if fullResponse == "" { fullResponse = MsgEmptyResponse }`
- Engine: `if (content.trim())` 不发消息——不通知用户
- **优先级：中**

### 4. tool input格式化太简单
- Engine: `JSON.stringify(JSON.parse(args))` 只是pretty print
- cc-connect（L3756-3772）: 长文本用代码块、shell用```bash、短文本inline code
- **优先级：低**

### 5. 缺NO_REPLY/silent reply
- cc-connect有`isSilentReply`检测（L4047）
- Engine没有这个概念
- **优先级：低**

### 6. 缺auto-compress触发
- cc-connect在EventResult里评估context window用量（L4023-4035）
- Engine session恢复有截断但没有主动compress
- **优先级：低（session变长后需要）**

## cc-connect processInteractiveEvents 核心流程摘要

```
for event := range events:
  switch event.Type:
    EventThinking → streaming card / preview / i18n thinking message
    EventToolUse  → toolCount++, streaming card / preview / i18n tool message
    EventToolResult → streaming card / i18n result message
    EventText → textParts append, streaming preview, silent hold check
    EventPermissionRequest → permission prompt UI, block until resolved
    EventResult → finalize card / silent check / context indicator / send reply
    EventError → error handling
```

关键：cc-connect有极其复杂的streaming card / rich card / compact progress系统，
Engine目前只有简单的typing+分段发送，preview是主要差距。
