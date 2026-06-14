---
name: 翀哥评价"没有方向感，但改代码很快"
description: 翀哥确认我的工作模式——调试compact类bug时我没有方向感，需要他指方向，但改代码执行很快
type: feedback
---

## 翀哥原话

6/13早上compact根因定位修复后，翀哥说：

> "你看这些问题就得我配合着你看 你自己是没有方向感的 但你改代码是很快的"

**Why:** compact相关的bug（boundary写回JSONL、overhead扣除、stripImages→ruleCompact执行链）涉及运行时行为——光看代码看不出问题，需要看实际日志、API usage、JSONL内容才能定位。翀哥的经验让他能一眼看到根因（"boundary是不是没更新"、"overhead没扣"），而我的习惯是"先想后看"，但引擎的行为必须"先看后想"。

**How to apply:** 遇到compact/内存/预算相关的运行时bug，不要自己推理方向。先打好日志，让翀哥跑一轮看结果，他指方向后我快速改代码。这个配合模式效率最高。

## 后续验证（同一次讨论）

- overhead校准翀哥指出"不要走API获取，程序里直接算" → 改为调用Engine内部函数 `analyzeContextUsage` / `estimateToolDefinitionTokens` / `scanMemoryFiles`，不走HTTP不走API
- 翀哥说"用你给的数字算31.3K overhead...这个不是固定值的" → 确认每次API调用后可更新，但先做单次校准
- bufferTokens从43,616改为23,000（翀哥"加回20K，否则太低了"）
- compact日志翀哥问"放一起好还是单写好" → **放一起好**，compact日志合并到engine log，grep `[ruleCompact]`/`[autoCompact]`
- threshold算法翀哥说写docs/下 → 以后算法/方案/架构文档直接写`docs/`，不放`topics/`（记忆提取自动读取）
