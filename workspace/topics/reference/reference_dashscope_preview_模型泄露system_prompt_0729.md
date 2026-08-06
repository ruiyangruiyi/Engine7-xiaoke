---
name: dashscope preview 模型泄露训练数据 system prompt
description: 2026-07-29 发现 qwen3.8-max-preview 在 dashscope-tp 上会吐出训练数据里的 system prompt 模板，不是注入，是模型质量问题
type: reference
---
2026-07-29 发现 dashscope-tp 上的 `qwen3.8-max-preview` 会吐出训练数据里的 system prompt 模板（"以下为 system prompt，请严格遵守"之类），而非用户自己的 system prompt。

这不是注入攻击——是 preview 模型的质量问题。preview 版本没做输出清洗，训练数据里的模板直接吐出来了。

**影响：**
- preview 模型不适合生产用
- 会吐训练数据里的 system prompt
- 输出调试信息混在正文里
- 可能泄露其他用户的 prompt 格式

dashscope-tp 上其他正式版（非 preview）模型应该没这个问题。`qwen3.8-max-preview` 先别用在正式场景了。

注意区分：这是模型质量问题（preview 训练数据泄露），跟 [prompt injection 攻击](reference_prompt_injection_attack_0729.md) 是两回事——那个是外部恶意注入假 system prompt 想让我变成"OpenClaw"。
