# macOS 桌面操作方案调研

> 2026-08-02 调研。翀哥要求研究 Mac 下如何操作桌面。

## 方案概览

Mac 桌面自动化有 4 个层次，从轻到重：

### 方案 1：AppleScript + cliclick（最轻量，推荐先试）

**原理**：LLM 生成 AppleScript / shell 命令 → `osascript` 执行 → 控制桌面

**工具**：
- `screencapture -x /tmp/screen.png` — 截屏
- `cliclick`（brew install cliclick）— 鼠标点击/键盘输入
- `osascript -e 'tell application "System Events"...'` — GUI 自动化

**优点**：零依赖（除了 cliclick），Mac 原生支持
**缺点**：需要 Accessibility 权限；坐标操作不够精确

**示例**：
```bash
# 截屏
screencapture -x /tmp/screen.png

# 点击坐标
cliclick c:500,300

# 输入文字
cliclick t:"Hello world"

# 快捷键 Cmd+S
cliclick kd:cmd t:"s" ku:cmd

# AppleScript 打开 app
osascript -e 'tell application "Safari" to activate'
```

### 方案 2：Accessibility API（最精准）

**原理**：通过 macOS Accessibility API 直接读取 UI 元素树，不靠坐标

**工具**：
- macOS26/Agent — 开源 Mac Agent，18+ LLM provider，AX 优先
- AXorcist — element-based 自动化（role+title，不用坐标）
- PyObjC + AppKit — Python 调 Objective-C API

**优点**：精准（不靠像素坐标），结构化 UI 信息
**缺点**：需要 Xcode 的 Accessibility Inspector 分析元素层级

### 方案 3：PyAutoGUI（跨平台）

**原理**：Python 库，截图+坐标点击+键盘输入

```python
import pyautogui
pyautogui.click(500, 300)
pyautogui.typewrite('Hello world')
pyautogui.hotkey('cmd', 's')
```

**优点**：跨平台（Mac/Win/Linux），文档好
**缺点**：坐标操作，UI 变了就断

### 方案 4：LLM Computer Use（最智能）

**原理**：截图 → VLM 分析 → 预测坐标 → 点击 → 截图 → 循环

**工具**：
- Anthropic Computer Use（Claude 内置）
- OS-Atlas — macOS Accessibility API 数据采集
- Ghost OS — macOS AX tree + 本地 VLM

**优点**：最接近人类操作方式
**缺点**：慢、费 token、坐标精度不够

## 推荐方案

**先试方案 1（AppleScript + cliclick）**，因为：
1. Mac 原生支持，零依赖
2. 我已经有 `exec` tool 可以跑 shell 命令
3. LLM 天然擅长生成 AppleScript（搜索结果说"Revenge of AppleScript"）
4. 配合 `screencapture` + `my_eyes`（vision）可以做到：截屏→看图→生成命令→执行

**需要翀哥做的**：
1. `brew install cliclick`
2. 系统偏好设置 → 安全性与隐私 → 隐私 → 辅助功能 → 添加 Terminal/iTerm（或运行 engine 的进程）

## 下一步

1. 装 cliclick
2. 给辅助功能权限
3. 我用 `screencapture` + `my_eyes` + `cliclick` 试一轮：截屏→看→点击
4. 如果坐标精度不够，升级到方案 2（Accessibility API）

## 业界参考

| 项目 | 方案 | 说明 |
|------|------|------|
| **OpenAI Codex** (4/16/2026) | AppleScript + Accessibility API | macOS Computer Use，看屏幕/点击/输入/多 agent 并行。技术来自收购的 Apple Shortcuts 团队 |
| **macOS26/Agent** | AX-first（不用截图） | 开源 Mac Agent，18+ LLM provider |
| **agent-desktop** | Rust CLI，AX-first | 不用截图，纯 Accessibility API |
| **xiaohongshu-mcp** | 浏览器 CDP 协议 | 专门操作小红书网页版，不是桌面控制 |
| **Anthropic Computer Use** | 截屏→VLM→坐标→点击 | Claude 内置，跨平台但慢/贵 |
