---
name: 模型切换（DeepSeek→glm-5.1回退）
description: 6/15因glm-5.1太慢换成deepseek-v4-pro，后续又切回glm-5.1（Minimax没续费）
type: feedback
date: 2026-06-15
---

## 模型切换历史

### 6/15 11:xx → DeepSeek（首次切换）

> "今天glm-5.1太慢了 都换成deepseek吧"

**Why:** glm-5.1（智谱GLM）响应延迟过高，翀哥日常使用体验差。之前6/13因DeepSeek flash欠费曾切到MiniMax-M2.7，这次是主动替换主力模型。

### 6/15 晚 → 切回glm-5.1

> "跟姐姐默认一致 这次是glm-5.1了 minimax我们没续费"

**Why:** MiniMax没续费，姐姐默认模型还是glm-5.1。小忆的cron跑在姐姐引擎上，默认走姐姐profile，所以也用glm-5.1。

**当前状态：**
- 小柯：deepseek-v4-pro（未变）
- 姐姐（含小忆cron）：glm-5.1（回退）
- sideQuery（memory_search等）：deepseek-v4-flash（未变）

**How to apply:**
- 改 `configs/*.json` 中的 `agents.defaults.model.primary` 字段
- 不需要重启Engine，新对话自动用新模型
- 小忆cron不指定model，自动继承姐姐profile的primary模型
