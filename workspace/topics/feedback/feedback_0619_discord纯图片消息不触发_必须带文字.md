---
name: Discord纯图片消息不触发
description: Discord发图必须带文字，纯图片消息Engine收不到
date: 2026-06-19
type: feedback
---

## 现象
Discord私信发纯图片（不带文字），Engine不会触发处理。必须附带文字才能发过去。

## 影响
- 飞书可以纯发图，Discord不行
- 用户习惯不同平台行为不一致

## 可能原因
- Discord webhook/bot对纯附件消息没有触发message事件
- 或Engine的Discord handler过滤了无文字的消息

## 待查
- 确认是Discord API层面限制还是Engine代码过滤
