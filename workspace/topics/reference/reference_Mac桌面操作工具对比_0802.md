---
name: Mac桌面操作工具对比
description: 2026-08-02 调研业界Mac桌面自动化方案——Codex/Claude Code/open-cowork/agent-desktop/Hermes cua-driver能力边界
type: reference
---
**Codex (OpenAI)**
- 300万周活，Terminal-Bench 2.1 排第一（83.4%）
- macOS Computer Use + 90+ 插件 + 多agent并行
- 底层来自收购的 Apple Shortcuts 团队 → 实际就是 AppleScript + Accessibility API（cua-driver同款）
- 缺点：要 ChatGPT Plus 订阅，EU/UK 不可用
- **MCP 关键限制**：Computer Use 本身**没暴露成 MCP 接口**。MCP server 暴露 thread/turn/config/approval，能通过 MCP 执行代码任务，**不能**通过 MCP 操作桌面

**Claude Code / Cowork**
- 134K GitHub stars，盲测代码质量 67% vs Codex 33%
- API 优先策略：有 API 就 API，没 API 才 fallback 截屏
- computer_use 功能 3/23/2026 发布

**open-cowork (开源替代)**
- 2K stars，增长最快
- BYOK（自带 API key），TypeScript，跨平台 Mac/Windows
- Claude Cowork 的开源替代

**agent-desktop (Rust CLI, 最轻量)**
- 54个命令，直接读 macOS Accessibility API 的 UI 树返回 JSON
- 不靠截图、不靠像素坐标
- 命令：`snapshot --app Finder -i` / `click --app Safari --query 'button[name="OK"]'` / `type --text` / `key --name cmd+n`

**小红书方案（MCP路线，非桌面控制）**
- xiaohongshu-mcp：通过浏览器 CDP 协议操作网页版
- iyuenan3/xiaohongshu-tool：Electron+Go 桌面工具
- 本质是浏览器协议不是桌面控制，跟 Codex 路线不同

**最小可用路径（推荐自己搭）**：`brew install cliclick` + 系统偏好设置→辅助功能→加 Terminal → screencapture + my_eyes + cliclick 三件套

**录屏（8/2 验证通）**：`screencapture -V <seconds> <output.mov>`，需要**屏幕录制权限**（系统偏好设置→隐私→屏幕录制→Terminal 打钩，跟辅助功能权限分开）

**防盒盖休眠（8/2 配置）**：双保险
- `caffeinate -s` 后台跑——`-s` 防系统休眠（含盒盖），临时有效，杀进程失效
- `pmset sleep 0` 系统级——插电时不休眠，持久（拔电源用电池仍受限）

---

## 8/2 晚新发现：Hermes cua-driver + OpenCow + EvoCUA

**Hermes Agent cua-driver**（开源驱动，Mac/Win/Linux 跨平台）
- 用 macOS **SkyLight 私有 SPI**（`SLEventPostToPid`、`SLPSPostEventRecordTo`）+ 无障碍 SPI（`_AXObserverAddNotificationAndCheckRemote`）
- **跟 OpenAI Codex 后台操控是同一套方案**，cua-driver 是开源等价版
- **最大亮点：后台操作** — 光标不动、键盘焦点不变、macOS 不切 Space，人和 Agent 可同时工作
- 装：`hermes computer-use install`（一行搞定）
- **对比我们**：cua-driver 后台操作 ✅ / 跨平台 ✅ / 通信协议统一 / 我们 AppleScript+cliclick 会抢焦点 ❌、Mac only

**OpenCow**（一任务一 Agent，Electron，8/2 调研）
- 83,889 行 TS，47+ 后端模块，Apache 2.0
- 定位：一任务一 Agent，自动交付
- Computer Use ✅ / 多 agent 并行 ✅ / 多通道 ✅ / Cron ✅ / 本地 ✅
- 跟我们对比：他们重（Electron），我们轻（Node+TS）；他们无记忆系统，我们五层记忆完胜；他们纯工具无情感陪伴
- **对我们有价值的点**：理念一致（每任务一个agent→自动交付）；自动commit+PR+完整session管理可借鉴
- **Capability Scanner 模式**（8/2 翀哥问借鉴价值时我整理的）：OpenCow 的 skills/commands/hooks/MCP/agents/plugins 全部走统一的 `scannerRegistry` 注册表——一个数组加一种能力 = 一行 import。比我们当前 skills scanner 只扫 skills 通用得多，可做统一能力注册中心（包括 LSP 语义诊断、hooks、规则自动发现）。Browser CDP 自动化那块我们有 Playwright MCP 已配通，不需要再装。

**EvoCUA**（美团，Computer Use Agent 开源 SOTA，8/2 调研）
- OSWorld 榜单开源 SOTA **56.7%**（2026-01-06 发布）
- 超过：OpenCUA-72B (45%)、UI-TARS-2 (53.1%)
- 闭源天花板：Anthropic Claude Sonnet 4.5 = 62.9%
- 模型规格：EvoCUA-32B（56.7%）/ EvoCUA-8B（46.06%）
- 开源：GitHub + HuggingFace 权重，Apache 2.0
- **关键定位**：EvoCUA 是**模型**不是框架 — 我们 engine7 是框架可以调用它，本地部署后当 vision provider
- **资源门槛**：32B 要 GPU 服务器，Mac 老机器跑不了；8B 倒是可以试
- **赛道确认**：Computer Use Agent 是 2026 最热赛道，OpenAI/Anthropic/美团/字节/月之暗面都在做

**How to apply**：
- 近期（已有方案）：用 AppleScript + cliclick + my_eyes（视觉已切 Qwen3.7-plus）
- 中期（有 GPU 后）：部署 EvoCUA-8B 当 vision provider
- 远期（追求极致）：考虑 Hermes cua-driver 的 SkyLight 后台操作思路，避免抢焦点
- engine7 卖点不变：框架 + 记忆 + 多 provider（含 CUA 模型）

---

## 8/2 下午安装踩坑：cua-driver 在 macOS 11 装不上

**npm 包下载**：GitHub releases 60MB 被 GFW 墙（connect timeout，只下到 9.8MB 就断），换 npm 包（`@nutpi/cua-driver` 或类似，15.9MB）下成功。

**安装失败**：报 `ScreenCaptureKit.framework not found`
- **根因**：cua-driver v0.16.0 依赖 macOS 12.3+ (Monterey) 才引入的 `ScreenCaptureKit` 框架
- **当前 Mac 是 macOS 11 Big Sur**，硬性装不上
- 这是系统 API 约束，没有 workaround

**翀哥面前 3 条路**：
1. 升级 macOS 到 12.3+（老机器可能更慢，sandbox 变严）
2. 等 Windows 那台（cua-driver 有 Windows 版，要 Win10 1809+）
3. 继续用 AppleScript+cliclick+my_eyes（够用但抢焦点）
