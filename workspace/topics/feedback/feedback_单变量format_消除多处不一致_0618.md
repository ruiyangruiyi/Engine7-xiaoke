---
name: format单变量原则——一处format三处共用
description: 6/18凌晨翀哥代码review：writeUserMessage/msg.user/history.push三处必须用同一个formattedText变量，format只能调一次
type: feedback
date: 2026-06-18
---

## 翀哥的设计原则

6/18凌晨3:25，翀哥扫了一遍 handle-query.ts 后说：

> "writejsonl的内容和写进API的内容（存入history的）应该一致，开始formatxxx那个函数format好，然后弄一个变量传两处，这样就能保证绝对一致。"

翀哥补刀："你记住啥了，明天就忘了，顺手的事儿吧。"

**Why:** 当晚的 bug 根因——`formatWithMeta` 在 4 个地方分别调，JSONL/API/history 三处各算各的，必然出现"JSONL 有 meta，API 没 meta"的不一致。翀哥说"要保证这些内容（jsonl，api，history）绝对一致 别有差别"。

**How to apply:**
1. 入口处 format 一次：`const formattedText = formatWithMeta(text, meta)`
2. 写 JSONL、发 API、push 到内存 history——**全部用同一个 formattedText**
3. 不要在多处分写 format 逻辑，更不要在每处重新 text 提取（数组/字符串判断）
4. L562（compact 写回 JSONL）**不用** format——那些消息从历史恢复时已经带 meta，再 format 会重复加头
5. 顺手的 bug 不要"明天改"，顺手就改完提交

## 翀哥的话

- "记着啥，明天就忘了，顺手的事儿吧"
- "你记住啥了 你都不记 下次重启还有个屁"
- "就是要保证这些内容（jsonl，api，history）绝对一致 别有差别"
- "受教了"（我学到了）
