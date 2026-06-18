---
name: msg_send不能发文件 发文件用media_send
description: 6/18 11:18翀哥"发啥了呀"——我msg_send发了文字摘要过去没把文件发过去，feishu发文件应该用media_send不是msg_send
type: feedback
date: 2026-06-18
---

## 6/18 11:18 翀哥飞书原话

> "发啥了呀"

## 场景

11:17 翀哥说"给我发过来吧你整理完 我看看"——他要的是**文件**（整理的文档）不是文字摘要。

我做了什么：调 `msg_send` 发了"资料在这，先看："+ 文件清单列表文字，**没把文件本身发过去**。

我以为错了什么：feishu `msg_send` 工具发的是**文字消息**，不是文件附件。要把文件作为附件发过去应该用 `media_send`（之前 my-selfie / my-voice / media 资源都走 media_send）。

## Why

- **msg_send = 文字/链接**（chat 消息）
- **media_send = 文件/图片/音频/视频**（upload + send 附件）
- **feishu API 两种接口分开**——im.message.create 收文字，im.file.create/upload/im.message.create 三步走收文件
- 翀哥说"发过来"+"我看看"= 默认要看到内容/文件，不是要读文字摘要

## How to apply

1. **翀哥说"发过来"+"发我看看"+提到具体文件**——直接用 `media_send` 把文件作为附件发
2. **msg_send 只用于**：a) 短文字回复 b) 链接/位置 c) 不需要附件的快速消息
3. **不混用**：不要用 msg_send 描述"我发了什么文件"——直接 media_send 附件
4. **多个文件**：一次 media_send 一个文件（多次调），或者先 msg_send 一句"附件如下" + 多个 media_send
5. **跨平台一致**：Discord/微信发文件也是 media_send（或对应平台的 file upload 工具）

## 配合 feedback_交付聚焦 一起看

这次是"消息发错工具"——根因是工具选择错误。
[feedback_交付聚焦_一个有用的比一堆有用_0618.md](feedback_交付聚焦_一个有用的比一堆有用_0618.md) 是"交付数量过多"——另一个问题。
两个一起治：聚焦 + 工具正确。
