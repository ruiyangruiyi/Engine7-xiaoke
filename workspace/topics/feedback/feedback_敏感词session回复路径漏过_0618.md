---
name: 敏感词过滤器session回复路径漏过——没挂在自动回复上
description: 6/18 09:36姐姐发现真正bug：过滤器只挂msg_send handler（AI主动发），session自动回复到群聊不走msg_send→不过滤。晓梅对话回复带敏感词直接发飞书群就漏了
type: feedback
date: 2026-06-18
---

## 6/18 09:36 姐姐报告真正bug

> "过滤器只挂在 msg_send handler 上，但 session 自动回复到群聊时不走 msg_send！"

## 两条 outbound 路径

1. ✅ **msg_send**（AI主动发）→ 过过滤器
2. ❌ **session 回复**（对话自动发到来源通道）→ **不过滤器** ← 漏的！

## 实际场景

晓梅在飞书群里收到翀哥消息 → LLM生成对话回复 → engine自动把回复发回飞书群 → **如果回复里带"老公"等敏感词直接发出去**，msg_send过滤器拦不到。

即使 09:23 修了 config 结构（`channels.group.sensitiveWords`），只要过滤器还只挂在 msg_send handler，session 回复路径就一直漏——**配置层和过滤路径是两个独立问题**。

## 修复方向（姐姐提出，翀哥未确认动手）

- session 回复路径也要过敏感词过滤
- 或者：回复发到群聊前统一走过滤检查
- 关键：**任何从 AI 发出到群聊的消息都要过过滤器**，不管 msg_send 还是 session 自动回复

## 6/18 09:42 姐姐进一步代码级定位

姐姐让看 main.ts（engine-startup）里 onResult/onText 回调怎么发到通道的，找到关键 bug 位置：

```ts
// L1725-1731（onResult 回调）
const response = content.trim() || '(任务完成)'
const delivered = await preview.finish(response)   // preview 可能直接发
if (!delivered) {
    channelManager.send(inbound.channel, inbound.channel_id, response)  // ← 直接 send，没过过滤
}

// L1682 / L1704 / L1715（onText 回调）：全都是 channelManager.send() 直接发
```

**`channelManager.send()` 是底层方法，不经过 msg_send handler**——msg_send 的敏感词检查对它完全透明。

**修法**（最干净）：把敏感词检查抽成公共函数，在 onResult 和 onText 里调。备选：让 channelManager.send 走 msg_send 的过滤链。

## 6/18 09:51 姐姐给的两个假设方向（已验证为假设2）

姐姐 09:41 给的排查方向：
1. **假设1：preview 流式输出匹配不到**——流式时一句话被分成多个 chunk，跨 chunk 敏感词匹配不到
2. **假设2：session 回复路径根本没读 sensitiveWords 配置**——msg_send handler 读 getSensitiveWords(resolvedSource)，但 session 回复走另一个代码路径没调这个函数

**实际验证**：假设2对。L1725-1731 onResult 回调里 `channelManager.send()` 直接发，**根本没调敏感词检查函数**——不是"读不到配置"，是"调用都省了"。

`preview.finish()` 也不一定过 filter（preview 是 freeze 状态保留）——所以 outbount 路径有三条：msg_send（有）、onResult+channelManager.send（漏）、preview.finish（取决于是否delivered，delivered时也算漏）。

## Why

之前设计 msgGuard 时只考虑了 AI 主动调 msg_send 工具发送的场景，没考虑 session 对话回复的"被动发送"路径。**漏了一条 outbound 路径 = 过滤器有洞**。

## How to apply

1. 任何 outbound 过滤（敏感词/限流/格式校验）不能只挂 msg_send handler，要考虑 session 自动回复路径
2. 设计消息出口时先列**所有 outbound 路径**（msg_send / session回复 / cron主动发 / webhook回执...），每条都要走相同的检查
3. 测试群聊场景要分别测：① AI主动发（msg_send）② AI对话回复（session自动）③ cron/heartbeat等系统消息
4. 姐姐发现的工程能力：她能从"产品行为"反推到"系统架构漏了哪条路径"——这种思路值得学
