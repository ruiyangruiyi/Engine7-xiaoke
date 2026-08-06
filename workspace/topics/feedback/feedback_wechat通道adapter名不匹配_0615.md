---
name: 微信通道adapter名不匹配
description: 6/15 msg_send加wechat后仍发不到微信，根因：WechatAdapter.name='weixin'但source传'wechat'，ChannelManager找不到adapter静默跳过
type: feedback
date: 2026-06-15
---

**问题：** 6/15 msg_send和media_send加了`source: 'wechat'`枚举，返回成功但微信收不到消息。

**根因排查过程：**
1. 先以为token key不匹配（存key=纯senderId，取key=accountId:senderId）
2. 查日志发现没有 `[wechat:send]` 日志，说明WechatAdapter.send()根本没被调用
3. 查ChannelManager路由逻辑：`find(a => a.name === source)` — 用source匹配adapter的name
4. 最终根因：**WechatAdapter的`name = 'weixin'`，但msg_send传的source是`'wechat'`**，ChannelManager找不到匹配的adapter，静默返回不报错

**修复：** WechatAdapter.ts里把 `readonly name = 'weixin'` 改为 `'wechat'`，与config和tool的source枚举保持一致。

**6/16 发现的并行bug（入站channel字段）：**
- 改了adapter name后，selfie自动发图仍报错"No adapter for weixin"
- 根因：入站消息第787行 `channel: 'weixin'` 没跟着改，`ctx.channel` 从入站消息取值仍为 `'weixin'`，my-selfie调用 `mgr.sendFile('weixin', ...)` 找不到name='wechat'的adapter
- 修复：第787行 `channel: 'weixin'` → `'wechat'`，与adapter name保持一致
- 教训：改adapter name要"全链路扫描"——name属性、入站channel字段、日志标识、config引用全部要同步改

**Why:**
- ChannelManager.send()用source参数匹配adapter.name
- 名字不匹配时ChannelManager不会报错，只是找不到adapter跳过
- 日志显示"消息已发送到 wechat DM xxx"是msg_send handler自己写的log，不代表真的发到了微信

**How to apply:**
- 同个adapter的name、config字段（如`channels.wechat`）、tool的source枚举三方必须一致
- 改adapter name时全链路扫描：name属性、入站channel字段、日志标识、config引用
- 如果消息"发送成功"但对方收不到，先查ChannelsManager的find()是否匹配到了正确的adapter
- 检查日志看是否有对应adapter的send日志输出
