---
name: voice-chat platform 化架构决策
description: voice-chat 应该作为 platform 接入 engine，跟飞书/Discord 平级，通过 scope 路由 session
type: project
---

# voice-chat platform 化架构决策

**日期：** 2026-06-27
**参与者：** 翀哥 + 小柯讨论确定

## 核心认知转变

之前把 voice-chat 当成"外部模块挂上去"，导致 session 路由断了。

**正确理解：** voice-chat 天生就是一个 channel/platform，跟飞书、Discord 平级。

## Session 路由方案

- **配了 `scope: main`** → voice-chat 消息进主 session，跟飞书私信/Discord 频道在同一个 session
- **没配 scope** → 走独立 session（当前状态，`voice-chat-session`）

### 配置方式

在 xiaoke.json 里：
```json
"session": {
  "dmScope": "main",
  "groupScope": "main"
}
```

voice-chat 的消息走同样的 scope 逻辑。配了 main → 进主 session；没配 → 独立 session。

## WebRTC 连接场景

### 本机场景（当前）
- 每个人跑自己的 engine，不同端口
- 浏览器连 localhost:port
- user_id 从配置文件读

### 外部场景（未来）
- 浏览器需要连一个信令服务器（固定的入口）
- 信令服务器根据登录身份把 WebRTC offer 转发到对应的 engine
- 类似 Discord gateway 的概念
- 现阶段不做，先搞本机

## 实现要点

1. voice-chat Python 层是 engine 的 platform adapter（不是外部模块）
2. ASR 文字走 engine 标准消息入口，带 platform=voice-chat + scope
3. engine reply 走 /voice-reply 接口（已在 server.py 中实现）
4. 本机场景不需要信令服务器，直接 HTTP POST offer

## 当前状态

- voice-chat 全链路（VAD→ASR→engine→voice-reply）已通
- 但 session 走独立的 `voice-chat-session`，没进 scope:main
- 待实现：把 voice-chat 接入 scope 逻辑
