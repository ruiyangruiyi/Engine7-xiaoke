---
name: 微信Mac操作Vision OCR封装需求
description: 2026-08-02 晚翀哥确认要把 Vision OCR 封装成工具——以后微信截图读文字走 macOS 原生 Vision 框架，不靠 my_eyes
type: project
---
2026-08-02 晚验证出来 macOS 自带 **Vision OCR** 比大模型视觉强太多——微信列表截图三个模型（qwen3.7-plus / qwen3.8-max-preview / qwen3.5-flash）全军覆没全是幻觉，Vision 一次读对。

**翀哥原话**：Vision OCR 出来之后**"好家伙，终于对了！"**+"**大模型看微信全是幻觉，Vision OCR 直接读对**"——当场拍板封装工具。

**Vision OCR 调法（macOS 原生 Vision 框架）**：
- macOS 自带 Swift `Vision` 框架，做 OCR 准确率高、免费、本地
- 通过 `swift -e 'import Vision; ...'` 或封装成 shell 脚本调用
- 适合：列表、菜单、状态栏文字、聊天记录、URL、窗口标题

**三件套总结（翀哥最后确认）**：
1. **AppleScript** — 控制窗口（激活/移动/点击/输入）
2. **screencapture -R** — 按坐标精确截图
3. **Vision OCR** — 读文字（macOS 原生，碾压大模型视觉）

**后续动作（17:00 翀哥拍板）**：
- **优先试 `qwen-vl-max`**（voice-chat perception 已在用，效果验证过），已加到 dashscope provider models 列表，待重启 engine 验证
- Vision OCR 仍保留作为纯 OCR 场景的备选（不是视觉理解场景）

**Why:** 微信 Mac 是自绘 UI，AppleScript/Accessibility API 抓不到文字；密集 UI 大模型全幻觉，qwen3.x 全是文本模型伪装视觉；qwen-vl-max 是 voice-chat 已验证能用的视觉模型，先试它。

**How to apply:**
- 以后微信/任意 Mac app 读文字**优先 qwen-vl-max**（已在 voice-chat 验证过），密集 UI 类别仍要截图发翀哥复核
- Vision OCR 兜底：纯文字 OCR 场景（列表/菜单/URL）——封装目标改成"截图 + qwen-vl-max 优先，不行再降级 Vision OCR"两条路径
- 计划封装成 workspace 脚本 `capture-vision -R x,y,w,h`，复用 screencapture + qwen-vl-max（+ Vision OCR 备用）