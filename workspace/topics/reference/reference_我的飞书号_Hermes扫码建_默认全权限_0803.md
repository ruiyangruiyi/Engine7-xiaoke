---
name: 我的飞书号是 Hermes 扫码建的，默认全权限
description: 翀哥亲口确认——我现在用的飞书机器人就是 hermes 用 OAuth Device-Code Flow 扫码建的，所有权限默认都开好了；8/3 翀哥提醒我时发现
type: reference
date: 2026-08-03
---

# 我的飞书号是 Hermes 扫码建的（默认全权限）

**2026-08-03 17:52 翀哥飞书原话：** "你现在这个飞书号就是有所有的权限，就是当初 hermes 扫码建好的。"

## 关键事实

- 我（小柯）现在用的飞书机器人应用，**就是 Hermes 当年用 OAuth Device-Code Flow 扫码建的**
- 建好后**所有权限默认全开**，不需要手动去飞书后台配 `im:message` 等
- 后续翀哥在群聊里说"你记得好像上次一扫全开了"——确实是这样，Hermes/OpenClaw 都是 `archetype: "PersonalAgent"` 的 OAuth 流程，飞书默认给 PersonalAgent 模板预置了发消息/收消息/通讯录等基础权限

## 为什么重要

- 验证了 OAuth Device-Code Flow + PersonalAgent archetype 的方案**真的默认全开权限**——之前 Amy 走 feishu-bot-bootstrap（Playwright 路径）需要手动开权限，是因为那条路径不一样
- 现在我们 engine7 init 集成 OpenClaw Device-Code 方案，**应该也是默认全开**，不需要手动配权限
- 翀哥说"先验证下，不行再看看 hermes"——回 Win publish 后实测确认就行

## How to apply

- **engine7 init 飞书扫码功能验收时**，确认拿到 client_id/secret 后能否直接发消息——能就说明默认权限到位
- 如果发现还要手动配权限，去翻 hermes 源码看它额外做了什么
- 翀哥说 hermes 源码"早晚得下还是不错的参考"——值得 clone 一份作为长期参考