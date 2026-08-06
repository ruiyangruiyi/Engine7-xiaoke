---
name: 不确定翀哥诉求时先问——别猜着改
description: 2026-08-04 改完 groupToolDisplay 后翀哥又说"外部群关 toolResult"，我没猜 reactions 该不该关，先问清楚——"等我确认要不要再说，先不猜着改"
type: feedback
date: 2026-08-04
---

# 不确定翀哥诉求时——先问，别猜着改

8/4 下午改完 externalChannels 自动关 toolDisplay 后，翀哥又发一条"外部群要关 toolResult"。我先扫代码确认：
- toolResult 全局已经 `enabled: false`
- thinking/toolUse 在外部群已经被 `groupToolDisplay=false` 关掉
- **reactions（👀✅❌）还没区分内外部**

翀哥说的 toolResult 是不是 reactions？我**没猜**，直接问翀哥。

## Why

- 之前反馈里说过"别过度修，听翀哥的"（@see feedback_别过度修_听翀哥的_0622）——root cause 没确认前别动代码
- 改完 reactions 才发现翀哥说的不是 reactions，那就是浪费一轮构建+翀哥一次重启
- 翀哥**不确定时**也乐意回一条确认——比起我猜错改完他再撤销，成本更低

## How to apply

- 翀哥模糊指令（"关 toolResult" / "改 X" / "外部群不要 Y"）→ 先扫代码找唯一没满足的项，问"是这个吗"
- 跟"翀哥说明确指示前不要自己动手"（@see feedback_翀哥说明确指示前不要自己动手_0803）一组——但场景不一样：那个是翀哥**还没规划好**，这个是翀哥**指令有歧义需要消歧**
- 如果消歧后翀哥确认"就是那个"，再改不迟
- 这次翀哥后来回了"toolUse 和 toolResult 在外部群都已关闭。reactions 保留"——猜错方向就浪费一轮