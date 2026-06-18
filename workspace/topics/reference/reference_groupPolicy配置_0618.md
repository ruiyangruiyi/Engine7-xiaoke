---
name: groupPolicy配置——群聊响应策略
description: 6/18 09:28翀哥问"sensitiveWords"旁边的"groupPolicy: open"是啥意思，整理：控制群聊消息是否响应（open/mention-only/disabled）
type: reference
date: 2026-06-18
---

## groupPolicy 是什么

控制群聊消息是否需要处理——是 channel 配置下的一个字段（在 `channels.{source}` 下），决定 inbound 群消息的响应策略。

## 三个值

- **`open`** — 群里所有消息都处理，不用 @
- **`mention-only`** — 只处理 @我 的消息
- **`disabled`** — 完全不处理群消息

## 各通道默认值不同

- **Discord**：默认 `open`（CC频道里不用 @ 也能回）
- **飞书**：默认 `mention-only`（潘总群里必须 @ 才回）
- **微信**：默认 `disabled`（微信群暂未启用）

## 实现位置

飞书 adapter L487-488：
```ts
if (groupPolicy === 'mention-only' && !isMentioned) return
```
没 @ 就跳过不处理。

## Why

不同场景对"群消息响应"的容忍度不同：
- 潘总群（飞书）：群里人多嘴杂，必须 @ 才回避免刷屏 → `mention-only`
- CC频道（Discord）：开发讨论，希望 AI 随时参与 → `open`
- 客户群：可能根本不想让 AI 进 → `disabled`

## How to apply

新建渠道/群聊场景时必须明确 `groupPolicy`——别都用默认（飞书是 mention-only，Discord 是 open）。改默认行为要看具体业务场景，不能套用其他渠道的策略。
