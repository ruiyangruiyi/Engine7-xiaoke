---
name: engine7 启动日志里哪些不是报错
description: 8/3 Amy 跑通后被两类正常日志吓到——ws reconnect 和 bot 回复时的 read/edit 工具调用
type: reference
date: 2026-08-03
---

# engine7 启动日志 / Bot 回复里的"正常噪音"

8/3 帮 Amy 跑通后，她在群里看到日志和回复里两类东西都被吓到了：

## 1. `ws connect failed` → `reconnect` → `ws client ready`（飞书 websocket）

**这是网络自动重连机制，完全正常。** 飞书长连接偶发断开会触发 reconnect，3 秒内自动恢复。看到这个序列不用担心——只要最后一行是 `ws client ready`，通道就是通的。

## 2. Bot 回复时显示 read / edit 文件

**这是 engine7 的 tool call 在工作，不是 bug。** 飞书把回复内容原样透传，tool call 调用的文件路径和内容会出现在消息流里——尤其是 inner-voice / SESSION-STATE 这类内部读写，bot 是在更新自己的状态文件，不是回复给用户的内容。

## 怎么告诉非技术用户

- 群里说"这些是正常的，你看机器人**能不能正常回复你**就行，不要看日志"
- 日志关心 `ws client ready` 和最后一行 `[channels] feishu connected` 这两个状态点
- Bot 回的内容看正面（是否有人话回复），不看背面（read/edit 是不是有）