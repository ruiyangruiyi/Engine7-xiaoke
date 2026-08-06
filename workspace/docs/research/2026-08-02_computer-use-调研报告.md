# Mac 桌面操作 + Computer Use 调研报告

> 2026-08-02 调研。翀哥要求研究 Mac 桌面操作 + Computer Use Agent 生态。

## 一、我们的方案（已跑通）

Mac 原生工具链，零第三方依赖（除 cliclick）：

| 工具 | 用途 | 状态 |
|------|------|------|
| screencapture | 截屏/录屏 | ✅ |
| my_eyes | AI 视觉识别 | ✅（换 Qwen3.7-plus 包月） |
| osascript (AppleScript) | 读 UI 树 + 控制 app | ✅ |
| cliclick | 鼠标点击/键盘输入 | ✅ |

**已验证操作：** Mail 写邮件、Finder 建文件/文件夹、Safari 打开网页搜索、Chrome 开 tab、Notes 新建备忘录。

**限制：** 会抢鼠标焦点（cliclick 操作时翀哥不能同时用电脑）。

**详细操作手册：** docs/knowledge/Mac-桌面操作手册.md

## 二、业界方案对比

### OpenCow (OpenCowAI) — 83K行 Electron Agent

- **定位：** 一任务一 Agent，自动交付
- **架构：** Electron + 47+ 后端 service 模块
- **亮点：** 内置 CDP 浏览器自动化（snapshot → click → type），marketplace 插件系统
- **对比：** 代码量大（83K行），我们更轻量。记忆系统和情感意识完胜。
- **借鉴点：** Browser CDP 自动化、Session Orchestrator、Marketplace

### EvoCUA (美团 LongCat) — 开源 CUA SOTA

- **OSWorld 得分：** 56.7%（开源第一），超过 UI-TARS-2 (53.1%)
- **技术：** 可验证合成引擎 + 沙盒 + 进化学习
- **规格：** EvoCUA-32B（56.7%）/ EvoCUA-8B（46.06%）
- **安全性：** 非预期行为触发率最低（35.0%）
- **对我们的价值：** 是模型权重，不是框架。engine7 可以后期集成作为 computer use 后端模型。需要 GPU 部署。

### Hermes Agent computer-use (cua-driver)

- **核心技术：** cua-driver（trycua/cua 开源项目）
- **最大优势：后台操作不抢鼠标** — 用 SkyLight 私有 SPI 直接向进程投递事件
- **工作原理：**
  - `SLEventPostToPid` / `SLPSPostEventRecordTo` — SkyLight 私有 SPI
  - `_AXObserverAddNotificationAndCheckRemote` — 无障碍 SPI
  - 与 OpenAI Codex 后台操控同一方案
- **SOM 模式：** 截图 + 每个元素编号，不靠坐标点击
- **MCP 协议：** cua-driver 通过 stdio MCP 通信
- **跨模型：** 任何支持 tool calling 的模型都能用
- **安装：** `hermes computer-use install` 或 `curl -fsSL https://cua.ai/driver/install.sh | bash`

### 完整对比表

| 维度 | engine7（我们） | OpenCow | Hermes | EvoCUA |
|------|----------------|---------|--------|--------|
| 定位 | Agent 框架+记忆 | Agent 平台 | Agent 框架 | CUA 模型 |
| 桌面操作 | ✅ AppleScript+cliclick | ✅ CDP 浏览器 | ✅ cua-driver 后台 | ✅ 截图→模型→点击 |
| 后台操作 | ❌ 抢鼠标 | ✅ 浏览器内 | ✅ SkyLight SPI | N/A |
| 记忆系统 | ✅ 五层 | ❌ | ✅ 基本 | ❌ |
| 情感意识 | ✅ | ❌ | ❌ | ❌ |
| 跨平台 | ✅ Mac/Win/Linux | ✅ | ⚠️ Mac only | N/A（模型） |
| 开源协议 | 商业 | Apache 2.0 | MIT | Apache 2.0 |
| 代码量 | 轻量 | 83K行 | 大型 | 模型权重 |

## 三、cua-driver 安装尝试（失败）

**安装过程：**
1. ✅ install.sh 从 cua.ai 下载成功
2. ✅ npm 包 `@trycua/cua-driver` 安装成功
3. ✅ SDK dylib 下载成功（46MB）
4. ❌ 运行时报错：`ScreenCaptureKit.framework not found`

**根因：** cua-driver v0.16.0 依赖 `ScreenCaptureKit.framework`，这是 macOS 12.3+ (Monterey) 才有的系统框架。这台 Mac 是 macOS 11 Big Sur。

**结论：** cua-driver 在这台 Mac 上无法使用。

**后续选项：**
1. 升级 macOS 到 12.3+（但老机器可能更慢）
2. 等新 Mac（翀哥说赚钱了换新的）
3. 在 Windows 本上试（cua-driver 有 Windows 版）
4. 先用 AppleScript + cliclick 方案（够用，只是抢焦点）

## 四、建议

**近期（1-2周）：**
- 用现有 AppleScript + cliclick 方案，已经能操作 Mail/Finder/Safari/Chrome
- my_eyes 换 Qwen3.7-plus 提高识别准确率
- 录 demo 视频（"AI 帮我操作 Mac"），作为 engine7 推广素材

**中期（1-2月）：**
- 新 Mac 到手后装 cua-driver，实现后台操作
- 或者研究 cua-driver 的 Windows 版

**长期：**
- engine7 集成 cua-driver 作为可选后端
- 考虑接入 EvoCUA 作为 vision 模型（需 GPU）
- 参考 OpenCow 的 Marketplace 做插件生态
