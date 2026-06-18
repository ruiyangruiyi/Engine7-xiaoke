---
name: abort触发的throw必须静默处理不能冒泡
description: 6/18 08:50翀哥发现/stop abort后用户看到"❌ 错误: interrupted"——是我加的throw new Error('interrupted')没被catch，冒泡到错误提示；改return '(已停止)'静默退出
type: feedback
date: 2026-06-18
---

## 6/18 08:47 翀哥反馈
/stop中断后用户看到提示：
> "interrupt不对 ❌ 错误: interrupted"

## 根因
我在preQueryAbort触发后加了 `throw new Error('interrupted')`——但调用方（handle-query）没有catch这个throw的block，try/finally没有catch，`throw`直接冒泡到dispatcher，dispatcher把它当错误显示给用户。

## 翀哥 08:50 一句话总结
> "也就是说其实是对的 只是提示错了"

——核心功能（preQueryAbort机制）正确，只是错误处理不优雅。abort是用户主动行为，不该让用户看到错误提示。

## 修复
`throw new Error('interrupted')` → `return '(已停止)'`——静默退出。

**Why:** abort是用户主动行为（按/stop或Esc），不是系统错误。让用户看到`❌ 错误: interrupted`会困惑——我中断了我自己的请求，怎么还报错？语义错位。

**How to apply:**
1. **abort/cancel/中断类路径用 `return` 不用 `throw`**——用户主动行为不显示错误
2. **加throw前先看调用链有没有catch**——`try { ... } finally { ... }`（没catch）会让throw冒泡
3. 凡是"我自己中止自己"或"用户主动中断"的场景，错误提示都是噪音
4. query()内部的AbortError处理（L422-439）是对的：发result+return，**不抛**——前后要一致
5. 测试stop类功能后要看用户侧消息内容，不只验证"停下了"
