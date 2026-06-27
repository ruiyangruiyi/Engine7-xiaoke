# 2026-06-27 voice-chat scope 路由接入

## 背景
voice-chat 全链路已通（VAD→ASR→engine→voice-reply），但 session 走独立的 `voice-chat:voice-chat-session`，没进主 session。原因是 bridge.ts 里 sessionId 硬编码拼接，绕过了 `resolvePlatformKey`。

## 方案
保持 plugin 注册不变，只复用 session manager 的 scope 路由机制。详见 [架构决策](../decisions/2026-06-27_voice-chat_platform化架构.md)

## 任务清单
- [ ] bridge.ts: `registerVoiceChatBridge` 加 `sessions` 参数，用 `resolvePlatformKey` 替代硬编码 sessionId
- [ ] plugin.ts: 把 `ctx.sessions` 传给 `registerVoiceChatBridge`
- [ ] rebuild + 重启验证：语音说话 → 主 session 收到（日志 `scope:main`）
- [ ] 提交代码

## 验证标准
1. engine 日志显示 voice-chat 消息进 `scope:main`（不是 `voice-chat:voice-chat-session`）
2. 语音说"小柯" → 我的主 session 能收到并回复
3. 回复通过 /voice-reply POST 回 Python（200 OK）
