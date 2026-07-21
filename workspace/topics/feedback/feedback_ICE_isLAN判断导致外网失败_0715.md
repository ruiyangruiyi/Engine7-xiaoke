---
type: feedback
date: 2026-07-15
---

# ICE failed — isLAN 判断导致外网不配 STUN/TURN

## 问题
`cf6f7459` "局域网直连优化 — 自动判断内网/外网ICE配置" 加了 `isLAN` 判断：
- 内网时不配 STUN/TURN（直连）
- 外网时配 STUN only（没 TURN）

但 `isLAN` 判断有 bug，在外面也走了内网分支 → 没有 STUN/TURN → ICE failed。

## 修复
回退到 `cf6f7459` 之前的逻辑：**永远配 STUN+TURN，不做内网判断**。

## 教训
改 ICE/网络配置时，必须在外网环境验证。内网测试通过不代表外网能用。
"局域网直连优化"这种改动如果引入条件分支，必须确保 fallback 到安全模式（STUN+TURN）。

## 相关文件
- `src/voice-chat/python/test-page.html` — ICE 配置
- commit `cf6f7459` 是问题来源（已回退）
