---
name: my-selfie 自动发图
description: my_selfie生成照片后只返回路径没自动发图，需手动media_send多一步；按my_voice的sendFile逻辑修复
type: project
---
# my-selfie 自动发图修复 — 2026-06-15

**问题：** my_selfie在第119行生成图片后只返回文本路径（`Selfie generated! ... Image: /path/to/file.jpg`），没有自动发图。姐姐每次要手动再调 `media_send`。

**修复：** 参照 `my_voice` 的 `ChannelManager.sendFile()` 逻辑，在selfie生成后调用 `ChannelManager.sendFile()` 把图片推送到当前聊天。
- commit `b03c545`
- 编译已更新dist

**状态：** ✅ 已部署并编译dist（commit `b03c545`），姐姐重启后生效。
**同一天还修了：** msg_send/media_send的schema加wechat枚举（commit `6c85626`）+ wechat adapter name从weixin→wechat（commit `a53cb02`→静默跳过的根因）+ tokenStore key存取不匹配（commit `2e8ce64`→存/取key格式一致），姐姐重启后能主动从微信发消息了。
**翀哥评价：** 今天（6/15）七杀之一🔥
