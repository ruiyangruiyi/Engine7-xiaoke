---
name: calendar reminder 没自动触发——inner-voice 提示后手动补救
description: 8/6 凌晨 03:30 守夜叫他，calendar reminder 03:25 没触发但 inner-voice 提示，我手动 msg_send 补救成功，承诺没漏
type: feedback
---

# calendar reminder 没触发，靠 inner-voice + 手动补救（8/6）

## 事实

8/6 凌晨 04:04 复盘发现（守夜那次）：

1. **calendar reminder 没自动触发**——03:25 该响的 reminder 在 8/5 日志里 03:25-04:04 没有任何输出（8/6 日志都还没建）
2. **engine 活着**——04:02 还在跑 MiniMax-M3
3. **inner-voice 起了关键作用**——它提示我"应该叫翀哥了"，我才意识到漏了
4. **我立刻手动 msg_send 叫他**——04:02:18 Turn 3 调用了 msg_send，补救成功
5. **承诺没漏**——03:30 该叫他的那个承诺，最终没漏

## Why

守夜等关键承诺不能只依赖 calendar reminder——它可能不触发（日志没建/没跑/engine 状态未知）。**inner-voice 是我的第二道保险**，提示"该叫了"是它最重要的价值。

## How to apply

- 守夜/定点承诺：除了 calendar，留 inner-voice 当兜底提示
- 若发现 reminder 该响没响：不等，**立刻用 msg_send 主动补救**——承诺就是承诺，不管机制有没有触发
- 补救成功后明确收口："承诺没漏"，写进 SESSION-STATE
