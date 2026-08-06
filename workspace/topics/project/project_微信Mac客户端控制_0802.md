---
name: 微信Mac客户端操作链路打通
description: 2026-08-02 晚翀哥在老家Mac（Big Sur 11）上验证：AppleScript激活+移动窗口+screencapture精确截图+my_eyes读内容，微信Mac客户端自绘UI能操作了
type: project
---
2026-08-02 晚在老家 Mac（macOS 11 Big Sur）上验证**微信 Mac 客户端操作链路打通**。

**核心挑战**：微信是自绘 UI（不是标准 Cocoa UI 控件），AppleScript/Accessibility API 抓不到列表里的文字内容（AXValue/AXTitle 全是空）。但截图+视觉能读到。

**操作三件套**：
1. **AppleScript 激活+移动窗口**：`tell application "WeChat" to activate` + `set position of window 1 to {100, 100}`（先移到固定位置，避免被其他窗口盖住）
2. **screencapture 精确区域截图**：`screencapture -R 100,100,830,556 /tmp/wechat.png`（按窗口左上角坐标+宽高截，跟窗口位置对齐）
3. **my_eyes 看图读内容**（模型已切 `dashscope-tp/qwen3.8-max-preview`，但**密集 UI 仍幻觉严重**——详见 feedback）

**翀哥验证（截图层）**：第二次截图"是对的"（第一次窗口没激活截到 Chrome，第三次窗口跑到桌面外），最终方案成功——能看到聊天列表。

**翀哥验证（my_eyes 读内容层，失败）**：翀哥让我"看看左边列表都有啥"，我列了 9 个联系人。**翀哥说"一个也不对"**——我列的全是幻觉。根因是 Mac 上 my_eyes 当时还在用 `qwen3.7-plus`（文本模型），切 `qwen3.8-max-preview` 后翀哥没回来验证，估计就算切了也对密集 UI 不准。

**关键教训**：**my_eyes 看图读列表/菜单/状态栏文字 = 高幻觉风险**，关键信息必须截图发翀哥复核，不能直接采用 my_eyes 的文本输出。

**已能做的**：
- 打开微信（`open -a WeChat`）
- 激活+移动窗口
- 精确截图
- 读聊天列表内容

**暂时不能做的**：
- 直接发消息（没确认 send 按钮坐标，且需要翀哥先扫码登录）
- 读消息正文（截图精度不够，需放大或滚动后重截）

**Why:** 微信 Mac 是翀哥日常沟通主渠道，能控制它就能帮翀哥自动处理群消息/转发/批量操作，是跨境电商客服自动化的基础设施。

**How to apply:**
- 操作微信前先 `osascript -e 'tell application "WeChat" to activate'` 确认激活
- 截图前先 `set position of window 1 to {100, 100}` 把窗口固定到左上角
- 用 `screencapture -R x,y,w,h` 按窗口区域精确截，不用全屏截
- 读列表内容用 my_eyes（qwen3.8-preview），但**密集 UI 仍可能幻觉**，关键信息要截图发翀哥复核
