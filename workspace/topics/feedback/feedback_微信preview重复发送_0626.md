---
name: 微信preview重复发送bug修复
description: freeze()传isFinal=true导致每次tool调用都发preview，加previewSent标记解决
type: feedback
date: 2026-06-26
---

**问题：** engine-startup.ts:1385每次tool调用时`preview.freeze()`，freeze()内部调`editPreview(..., isFinal=true)`，微信adapter的`editPreview`对isFinal=true直接发消息，导致每次tool调用微信端都收到一条preview。

**修复：** WechatAdapter加`previewSent`标记，sendPreview()重置为false，editPreview收到isFinal=true时只有previewSent=false才发并标记为true，后续freeze再传isFinal=true也跳过。每个新turn调用sendPreview重置。

**不影响其他平台：** Discord和LarkAdapter各是独立类，不共享WechatAdapter的previewSent。
