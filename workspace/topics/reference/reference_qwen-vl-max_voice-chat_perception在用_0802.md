---
name: qwen-vl-max 在 voice-chat perception 里已用过
description: 2026-08-02 翀哥提醒 qwen-vl-max 已经在 voice-chat 的 perception 模块里用了——以后 mac 看图换这个，不用走 Vision OCR 退化方案
type: reference
---
2026-08-02 17:00 翀哥原话："qwen-vl-max 你可以试试这个，我们在 voice-chat 的 perception 里用了"。

也就是说 engine 里 voice-chat 模块**已经在用 qwen-vl-max 做视觉**，并且能用——只是 my_eyes 工具的 model 配错了（用了 qwen3.7-plus/qwen3.8-max-preview 文本模型，不是 VL 系列）。

**Why:** 验证过能用且已经在用——意味着不用"探索未知模型"，直接把 voice-chat perception 里那个 provider 的 model id 拷过来给 my_eyes 用就行。

**How to apply:**
- 任何需要"看图"的工具（my_eyes / my_selfie 内容校验 / perception 等），默认走 `qwen-vl-max`
- 切之前先 voice-chat perception 那边确认 model id 一致
- 如果 qwen-vl-max 也不好使，再退到 macOS Vision OCR（纯粹 OCR 任务 Vision 更强，"理解图片"还是得 VL 模型）
