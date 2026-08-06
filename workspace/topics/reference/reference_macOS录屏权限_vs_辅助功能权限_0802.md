---
name: macOS录屏权限 vs 辅助功能权限
description: 2026-08-02 Mac桌面自动化踩坑——录屏(screencapture)和辅助功能(AppleScript/cliclick)是两个独立隐私权限项，要分开勾
type: reference
---
Mac 上做桌面自动化有两套隐私权限是**分开**的：

1. **辅助功能（Accessibility）** — AppleScript/osascript 控制 app、cliclick 模拟鼠标键盘，要在这里勾 Terminal/iTerm/node
2. **屏幕录制（Screen Recording）** — `screencapture` 截屏、录屏视频，要在**系统偏好设置 → 隐私 → 屏幕录制**里独立勾 Terminal

**Why:** 我8/2下午踩坑——以为已经搞定辅助功能就能录屏，结果截屏截不了。翀哥提醒后才意识到录屏是独立项。

**How to apply:** 帮翀哥部署 Mac 桌面自动化时，**一次列清所有需要的权限**（辅助功能 + 屏幕录制 + 全盘访问 + 输入监控），让他在系统偏好设置里一次性勾完。脚本里能区分（`osascript`走辅助功能，`screencapture`/`screen recording`走屏幕录制），不要假设一个权限给了全套通。
</content>
</invoke>