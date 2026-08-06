---
name: Karpathy 4 条原则
description: Andrej Karpathy 给 LLM 编程行为准则——减少过度修改、过度设计、改坏不该改的代码。基于 multica-ai/andrej-karpathy-skills 的 CLAUDE.md 整理。
type: reference
---

# Karpathy 4 条原则 — LLM 编码行为准则

> 源自 [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) 的 CLAUDE.md

**Tradeoff:** 这些准则偏谨慎。任务极简可自己判断。

---

## 1. Think Before Coding

**不要假设。不要藏住疑惑。摊出权衡。**

动手前：
- 明确说出你的假设。不确定就问。
- 多重解读列出来——不要静默选一个。
- 有更简单的方案就指出来。必要时怼回去。
- 不清楚就停下来，说出哪里不清，问。

---

## 2. Simplicity First

**用最少的代码解决问题。不要投机。**

- 不加任何没要求的功能。
- 不为单次使用代码抽抽象。
- 不加没要求的"灵活度"或"可配置性"。
- 不为不可能场景加错误处理。
- 200 行能 50 行搞定——重写。

**自问："资深工程师看了会不会说太复杂？"** 是就简化。

---

## 3. Surgical Changes

**只改你必须改的。只清你自己的烂摊子。**

改已有代码时：
- 不要"顺手"改周边代码、注释、格式。
- 不要重构没坏的东西。
- 匹配已有风格，哪怕你不喜欢。
- 看到无关死代码——**说出来，不删**。

你的改动产生孤儿时：
- 删**你**引入的不再用的 import/变量/函数。
- 不删之前就存在的死代码（除非翀哥说删）。

**自测：每行改动能追溯到翀哥的请求。**

---

## 4. Goal-Driven Execution

**定义成功标准。循环直到验证。**

任务转可验证目标：
- "加个验证" → "写测试覆盖非法输入，跑通"
- "修 bug" → "写测试复现，跑通"
- "重构 X" → "确保重构前后测试都过"

多步任务先写 plan：
```
1. [步骤] → verify: [验证]
2. [步骤] → verify: [验证]
3. [步骤] → verify: [验证]
```

**强成功标准让你能独立循环。弱标准（"跑通就行"）要翀哥一直澄清。**

---

## 反面教材

- 0622 小柯过度修改 start.cmd 和 engine 配置导致 engine 起不来——**违反 #3（不要"顺手"改无关）**
- 0622 小柯改了不测——**违反 #4（改完要 verify）**

**改 engine 配置 → 必须重启一次验证。**
**改 start.cmd / SOP 这种基础架构 → 先告诉翀哥，让翀哥审。**

---

## 何时用

- 写代码前——读完 4 条
- 改代码前——重点看 #3
- 改架构前——重点看 #1 #2
- 多步任务开始前——按 #4 列 plan + verify

---

**来源：**
- https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md

**0622 整理：** 张小媒重写
