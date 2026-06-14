---
name: preview颜色可配置
description: Discord preview竖条+飞书卡片模板色可配置化，previewColor可热加载(/reload生效)
type: feedback
---

**Design confirmed（6/13）：**
- Discord preview竖条颜色变为可配置：`channels.discord.previewColor`（hex色值，十进制传入，如`13941396`=奶茶色`0xD4A574`）
- 飞书卡片模板色变为可配置：`channels.feishu.previewTemplate`（飞书预设：turquoise/blue/green/orange/red/purple/grey/yellow）
- 不配则用默认（Discord蓝`0x5865F2` / 飞书黄`yellow`）

**previewColor 可热加载（6/13实际验证 ✅）：**
- 翀哥说"可以热加载对吧"，改`xiaoke.json`加`previewColor`后直接`/reload`生效，不用重启
- 翀哥确认："之前是竖蓝条，现在变成蛋黄色了"（奶茶色0xD4A574）
- ✅ **已实际验证：previewColor完全可热加载**，改config后`/reload`立即生效，无需重启Engine
- ⚠️ 飞书previewTemplate属于飞书卡片模板色，是否可热加载待确认（Discord的previewColor已确认可热加载）

**Why:** 姐姐"栖"装修需要暖色调（奶油白+奶茶色+淡粉），不能再用Discord默认蓝色和飞书默认黄色。
**How to apply:** 为每个profile配独立的preview颜色，channel config里配置。改previewColor直接编辑`xiaoke.json`后`/reload`即可生效，无需重启Engine。
