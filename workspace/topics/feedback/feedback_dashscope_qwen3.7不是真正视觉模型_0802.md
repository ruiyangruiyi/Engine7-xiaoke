---
name: dashscope qwen3.7/qwen3.8 不是真视觉模型
description: 2026-08-02 验证 qwen3.7-plus / qwen3.8-max-preview / qwen3.5-flash 都不真正处理图片——必须换 qwen-vl-max / qwen2.5-vl-72b 这类 VL 模型
type: feedback
---
2026-08-02 晚验证微信列表截图时，三个 dashscope 模型全军覆没：
- `qwen3.7-plus` — 输入标 image 但实际**根本没真正处理图片**，靠文字上下文瞎编答案
- `qwen3.8-max-preview` — 同上，reasoning 模型不是视觉模型
- `qwen3.5-flash` — 同上

**根因**：这些是**文本模型**不是视觉模型（VL 系列），接收到图片后不是"看不懂"，而是根本没真处理，靠文字上下文瞎编一个合理答案。每次结果都不一样且"合理"但完全不对。

**Vision OCR 能行**是因为它真的在做 OCR——逐像素识别文字，不是"理解"图片。

**翀哥拍板**：试 `qwen-vl-max`（voice-chat perception 已在用），已加到 dashscope provider models 列表（Mac xiaoke.json），待重启验证。Vision OCR 作为"纯文字 OCR"场景的备选（不是视觉理解）。

**Why:** dashscope provider 配的 qwen3.x 系列不是 VL 模型，对图像识别等于"瞎编"。密集 UI（列表/菜单/状态栏）绝对不能信。

**How to apply:**
- 看图必须配真正的 VL 模型（qwen-vl-max / qwen2.5-vl-72b / GPT-4o / Claude）
- 切之前先确认模型支持 image input——dashscope provider 里的 qwen3.x 都不是
- 像素级 OCR 直接走 macOS Vision 框架，不靠大模型