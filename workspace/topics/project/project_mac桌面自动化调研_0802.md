---
name: Mac 桌面自动化调研
description: 2026-08-02 翀哥让我调研 Mac 桌面操作方案，让他/我能操作桌面 app
type: project
---
2026-08-02 早，翀哥提需求——让我能操作 Mac 桌面（截图→看屏幕→点按钮→输文字）。

**调研发现的 4 条路：**
1. **`screencapture` + `cliclick` + my_eyes** — 截屏→模型看图→cliclick点击/输入（最轻量）
2. **`osascript` 跑 AppleScript** — 直接控制 app
3. **Codex 的 macOS Computer Use**（4/16 更新）— 底层就是 AppleScript + Accessibility API，OpenAI 收购 Apple Shortcuts 团队做的
4. **小红书 MCP** — 走浏览器 CDP 协议，跟桌面控制本质不同；不适合通用场景

**重点发现：agent-desktop（Rust CLI，最推荐）**
- 直接读 macOS Accessibility API 的 UI 树，**不靠截图、不靠像素坐标**，返回 JSON
- 54 个命令：snapshot/click/type/key/clipboard/window
- `agent-desktop snapshot --app Finder -i` 看当前 UI 结构
- `agent-desktop click --app Safari --query 'button[name="OK"]'` 按语义点击
- `agent-desktop type --text "hello world"` 输入文字

**翀哥的判断：** Mac 上操作桌面更接近 Codex 那条路，不走小红书 MCP。

**待执行：**
- `brew install cliclick`
- 系统偏好设置→隐私→辅助功能→添加 Terminal
- 装完即可做截屏→看→点→输入整套操作

**调研文档：** `docs/research/2026-08-02_mac-desktop-automation.md`

**Why:** 翀哥想让我能自动化操作 Mac 桌面，扩展小柯的能力边界到 GUI 应用层
**How to apply:** 翀哥后续提 Mac 桌面操作需求时，从 agent-desktop（语义操作，最稳）和 cliclick+my_eyes（视觉操作，最轻量）两条路选，不要走小红书 MCP 那条（场景不符）