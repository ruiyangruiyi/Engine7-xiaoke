---
name: maskFilter子agent结构化content需提取Result字段
description: 6/21 小柯发现general-purpose子agent返回的content包含Scope/Result/Key files结构化格式，maskFilter直接用了整个content会泄露内部格式到外部群
type: feedback
---

6/21 口罩Agent上线后，小柯主动检查发现：maskFilter用 `subAgent.run({ prompt })` 调子agent过滤，但general-purpose子agent的system prompt要求输出 `Scope / Result / Key files / Issues` 结构化格式（跟runAgent的通用prompt模板一致）。

所以 `result.content` 返回的是包含结构化字段的完整文本，maskFilter直接把这个整个content赋给了 `finalResponse` → 外部群收到的消息会带Scope/Key files等内部格式。

修复：用正则 `/Result:\s*([\s\S]*?)(?=\n(?:Key\s+files|Issues|Scope)|\n*$)/` 提取Result字段的纯文本。

**Why:** runAgent创建的子agent默认使用general-purpose prompt模板，该模板要求结构化输出。如果用子agent做过滤/翻译等处理，子agent的最终回复会包含Scope/Result/Key files/Issues标签。

**How to apply:** 任何用 `subAgent.run()` 或 `runAgent()` 处理文本的场景，如果只需要纯文本结果：
1. 检查子agent的prompt模板是否要求结构化输出
2. 是的话从 `result.content` 中提取 `Result:` 字段的内容
3. 或者传自定义prompt覆盖通用模板的结构化要求
