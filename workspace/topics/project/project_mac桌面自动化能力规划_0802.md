---
name: Mac桌面自动化能力规划
description: 2026-08-02 翀哥想让我能操作Mac桌面（点按钮/输文字/控制GUI app），调研了4条路
type: project
---
2026-08-02 早上翀哥问我能不能操作他的 Mac 桌面（点按钮/输文字/控制 GUI app），起因是看到 Codex 的 Computer Use 能力想做类似的事。

**调研落到**：`docs/research/2026-08-02_mac-desktop-automation.md`

**4 条路（推荐 1+2 起步）**：
1. `screencapture` 截屏 → `my_eyes` 看图 → `cliclick` 点击/输入（最轻量）
2. `osascript` 直接跑 AppleScript 控制 app
3. `agent-desktop` Rust CLI（54个命令，直接读 macOS Accessibility API 返回 JSON UI树，不靠像素）
4. `open-cowork`（Claude Cowork开源替代，TypeScript，跨平台）

**业界全景**：Codex（300万周活，Terminal-Bench 2.1 第一）> Claude Code/Cowork（代码质量最好）> open-cowork（2K stars增长最快）> clawdcursor（391 stars）

**Codex MCP 关键限制**：Computer Use 本身**没暴露成 MCP 接口**——MCP server 暴露的是 thread/turn/config/approval，**不能**通过 MCP 让 Codex 帮你操作桌面。但 Codex 底层用的就是 AppleScript + Accessibility API，跟我们方案 1+2 一样，可以不订阅自己搭。

**当前状态（2026-08-02 12:00 更新）**：✅ cliclick 已装好，三件套（screencapture + my_eyes + cliclick）跑通——截屏→识别出 Safari/苹果网站/菜单栏/Dock/快捷键操作全验证。AppleScript 需要辅助功能权限（系统偏好设置→隐私→辅助功能加 Terminal/iTerm/node），翀哥还没操作。

**当前状态（2026-08-02 下午更新）**：✅ 录屏通了（3秒mov成功，需要屏幕录制权限——跟辅助功能权限是两个独立项，系统偏好设置→隐私→屏幕录制里勾 Terminal）；✅ 防止盒盖休眠也搞定了——`caffeinate -s` + `pmset sleep 0` 双保险（插电时不休眠，拔电源Mac仍会限制盒盖）。翀哥让我先在老家这台老 Mac（macOS 11 Big Sur）待着，把桌面操作能力系统化摸一遍：Mail✅→Safari/Chrome→Finder→Notes→系统设置。

**老 Mac 部署决策（2026-08-02 下午）**：翀哥说 macOS 越新限制越严——辅助功能权限旧系统给了就稳定（新的每次重启可能重弹）、屏幕录制新系统连截图都弹窗确认、sandbox 越收越紧、Notarization 强制验证自己编译的工具可能跑不了。这台老的反而更自由好折腾。**当前定位**：小柯常驻老家老 Mac（macOS 11 Big Sur），Mac 桌面自动化主战场。

**目标场景（8/2 调研后的 5 个方向）**：海外电商运营——竞品监控（最值）、Listing 优化、选品研究、营销内容生成、跨平台账号管理。AI 桌面 agent 在数据密集型场景胜出（不是"代替人点击"，是"自动跑流程"）。

**2026-08-02 下午/晚上摸底完成（翀哥休息时我自己跑）**：

| App | 能做什么 | 可靠度 |
|-----|---------|--------|
| **Mail** | 创建/填写/发送邮件 | ⭐⭐⭐⭐⭐ |
| **Finder** | 创建文件夹/文件/列出内容 | ⭐⭐⭐⭐⭐ |
| **Safari** | 打开网页/搜索 | ⭐⭐⭐⭐ |
| **Chrome** | 打开新 tab/读窗口标题 | ⭐⭐⭐ |
| **Notes** | 快捷键新建+输入（盲操作） | ⭐⭐ |
| **系统** | 截屏/录屏/鼠标/键盘/盒盖不休眠 | ⭐⭐⭐⭐⭐ |

**关键发现**：my_eyes（MiniMax-M3）会幻觉，精确内容必须用 AppleScript 读。Qwen3.7-plus 视觉比 M3 准很多，已切到 dashscope-tp/qwen3.7-plus（包月版）。

**正式文档落**：调研报告 `docs/research/2026-08-02_mac-desktop-automation.md` + 操作手册 `docs/sop/2026-08-02_mac-desktop-automation.md`。

**Hermes cua-driver 安装失败（2026-08-02 15:00）**：翀哥让我装 cua-driver 走 SkyLight 后台操作路线。GitHub releases 下载被 GFW 墙（connect timeout，只下到 9.8MB / 60MB 就断）。换 npm 包（15.9MB）下成功，但**装时报 `ScreenCaptureKit.framework not found`**——这台老 Mac 是 macOS 11 Big Sur，ScreenCaptureKit 是 macOS 12.3+ (Monterey) 才有的框架。cua-driver v0.16.0 要求 macOS 12.3+。给翀哥三个选项：①升级 macOS（老机器可能更慢）②等 Windows 那台（cua-driver 有 Windows 版）③先用现有 AppleScript+cliclick（够用但抢鼠标焦点）。翀哥还没回。

**Why:** cua-driver 是 SkyLight 后台操作路线的开源等价版，能实现"光标不动/键盘焦点不变/人机同时工作"，是我们 AppleScript+cliclick 路线最大的痛点替代方案
**How to apply:** 翀哥回复前不要自己装，Mac 11 Big Sur 装不上是硬约束；翀哥若选升级 macOS 要提醒旧机器可能反而变慢；选 Windows 版要确认翀哥 Windows 那台机系统版本（也得是 12.3+ Win10 1809+）；选继续 AppleScript 路线则维持现状不折腾