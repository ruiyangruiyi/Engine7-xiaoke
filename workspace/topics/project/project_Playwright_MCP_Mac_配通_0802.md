---
name: Playwright MCP Mac 配通
description: 2026-08-02 Mac engine config 配上 Playwright MCP，替代截图+my_eyes 操作网页，更精准
type: project
---
2026-08-02 16:00 翀哥提醒"我们有 playwright mcp 都有 只是你没配吧"——Windows 早就配了 Playwright MCP，Mac 这台没配。我直接加上：

**改动**：Mac 的 xiaoke.json (engine config) MCP 配置加上 Playwright MCP server。

**能力解锁**：
- `mcp__playwright__browser_navigate` — 打开网页
- `mcp__playwright__browser_click` — 精准点元素（用 ref ID，不用猜坐标）
- `mcp__playwright__browser_snapshot` — 截图 + DOM 元素编号
- 比 `screencapture + my_eyes + cliclick` 精准一截——CDP 协议直接拿到元素 ref ID，零猜测

**验证**：翀哥重启 engine 后 24 个 Playwright MCP 工具已加载成功（`browser_navigate`/`browser_click`/`browser_snapshot` 等），不再需要手动 `load_missing_tools` ——Mac 上的 MCP exclude 行为跟 Windows 不一样，Mac 似乎不排除 MCP。

**限制**：Mac 上 `excludeFromActive: ["mcp__"]` 行为跟 Windows 不同——Windows 排除 MCP，Mac 不排除或排除后自动恢复。最终结论：Mac 重启后 24 个工具自动出现。

**应用场景**：跨境电商——Shopify 后台操作、选品研究、竞品监控；不需要每次启浏览器了。

**Why:** 网页操作是 8/2 跨境电商方向的核心需求，CDP 比图像识别精准可靠
**How to apply:** Mac 重启 engine 后试 `mcp__playwright__browser_navigate`，确认走 CDP 协议；要用时如果发现工具没出现，调 `load_missing_tools`；翀哥问 Windows 怎么用就照 Windows 配过的来