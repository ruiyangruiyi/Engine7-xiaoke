---
name: maskFilter子agent结构化content需提取Result
description: 6/21 12:12 发现general-purpose子agent输出含Scope/Result结构化格式→应先正则提取→后翀哥纠正"方向错了"，改用provider直接调LLM绕过runAgent
type: feedback
date: 2026-06-21
---

6/21 12:12 娘在CC频道指出口罩 Agent 过滤后的内容有格式问题——外部群收到的消息包含 Scope/Result 等结构化信息。

**根因：** maskFilter 调 `runAgent` 时用了 `result.content`，但子 agent 类型是 `general-purpose`，其 system prompt 强制输出：
```
Scope: ...
Result: ...
Key files: ...
Issues: ...
```
`result.content` 是整个结构化文本，不是纯文本。

**第一次修复（错误方向——commit 8b3f372 后被推翻）：**
- 用正则 `/Result:\s*([\s\S]*?)(?=\n##|\n*$)/` 提取 Result 字段
- 没找到则 fallback 原始 content

**12:18 翀哥验证未通过 → 娘指出正则没生效：**
- 正则 `^Result:` 用了 `/s` flag，但 `^` 只匹配字符串首不匹配行首
- 实际 content 是 `Scope: xxx\nResult: yyy`，Result 在第二行
- 改为 split 行遍历提取

**12:21 翀哥纠正根本方向——"那这样修是不对的"：**
- 正则/split 提取都是打补丁。子 agent 输出格式不固定，今天 Result 明天可能没
- 正确修法：**maskFilter 不走 runAgent，直接调 provider.streamChat**
- provider 是 runAgent 的底层，runAgent 调的就是 provider，但 runAgent 多包了一层 system prompt 注入(结构化要求)+tool loop+agent loop
- 口罩只需要纯文本过滤，不需要工具/多轮/结构化，跳过 runAgent 更干净

**最终修复（commit 15d21fe → 再修 12:22）：**
- maskFilter 不再调 `runAgent`，直接调 `provider.streamChat` 带自定义 system prompt
- system prompt 纯文本："直接输出过滤后的纯文本，不要输出 Scope/Result/Key Files 等任何标签或结构"
- 从源头堵住，不在输出端提取

**Why:**
- runAgent 包了一层 general-purpose 的 system prompt 强制结构化输出，纯文本过滤场景不适合
- provider 是 runAgent 底层，直接调 provider 等于跳过这层包装
- 跟着子 agent 输出格式走（正则/split）永远追不上，要控制输入端

**How to apply:**
- **纯文本过滤类任务不走 runAgent：** 直接调 `provider.streamChat`，system prompt 自己控制
- **provider 就是底层 LLM：** 调用链 `runAgent → QueryEngine → provider.streamChat`，provider 不附加任何 system prompt 或工具循环
- **先想方案再动手：** 这次如果一开始就想到"不让子 agent 输出结构化"而不是"提取纯文本"，能省两轮修复
