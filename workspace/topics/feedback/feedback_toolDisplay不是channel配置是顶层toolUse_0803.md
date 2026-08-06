---
name: toolDisplay不存在_关调试改顶层toolUse.enabled
description: 2026-08-03 Amy 关调试信息时我先猜"channel.toolDisplay"，翀哥纠正——关调试显示要改顶层 toolUse.enabled=false，不在 channel 里
type: feedback
date: 2026-08-03
---

# 关调试显示的配置位置（翀哥纠正）

**事实：** Amy 嫌群聊里一直显示 🔧 工具调用想关掉，我下意识让她搜 `toolDisplay` 字段——Amy 找不到，我又让她在 channel 里加 `toolDisplay: false`——翀哥打断说："不是 channel 里那个，是顶层 `toolUse` 配置"。

**真正的配置：** main7.json 顶层
```json
"toolUse": {
  "enabled": true,
  "emoji": "🔧",
  "displayMode": "raw",
  "bashDisplayMode": "both"
}
```
`enabled: false` 就关掉所有 🔧 工具调用显示。

**Why:** 我混淆了 display 配置的层级——没有 `toolDisplay` 这个字段，display 是顶层 `toolUse` / `toolResult` / `preview` / `reactions` / `thinking` 五大块，关 tool 调用要改 `toolUse.enabled`。

**How to apply:**
- 以后非技术用户嫌工具信息刷屏——直接告诉她改 `toolUse.enabled` 为 false，不存在 `toolDisplay`
- Amy 改不了配置文件，我改好 main7.json 直接发群里让她 copy 覆盖——比手把手教她改 JSON 靠谱
- 完整 display 配置表见 [reference/reference_display配置.md]