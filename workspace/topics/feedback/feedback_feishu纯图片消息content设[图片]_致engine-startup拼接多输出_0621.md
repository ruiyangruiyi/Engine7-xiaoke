---
name: feishu纯图片消息content设空字符串，engine-startup已拼了
description: 6/21 feishu.ts纯图片时content填'[图片]'，engine-startup trim()判断为truthy，把'[图片]'当用户文字拼进meta前缀后，多输出一行
type: feedback
---

## 事件
2026-06-21 14:11 翀哥发测试图片，验证 my_eyes 后我看到的 description 多了一行。

## 根因
feishu.ts line 549：纯图片消息（无文字）时，`content` 被填成 `'[图片]'`。

但 engine-startup.ts line 1736-1738 用 `inbound.content.trim()` 判断有无文字：
- truthy（`'[图片]'` 非空）→ 走第一条分支，把 `[图片]` 也拼进 meta 前缀
- 用户实际只发了图没发文字，但 meta 里多了 `[图片]` → 多输出一行

## 修复
feishu.ts：纯图片消息时 content 设空字符串 `''`，不填 `[图片]`。
engine-startup 的 trim() 判断自然走纯图片分支 → 只输出 `[meta:xxx] 路径：xxx`，不多一行。

**Why:**
- content 语义应该是"用户输入的文字"，不是"无文字时的占位符"
- engine-startup 层已经有 `trim()` 判断了，两层的占位判断冲突

**How to apply:**
- adapter 层 content 字段只放用户真实输入的文字
- 无文字时设空字符串，不要设"图片""文件"等占位说明
- 占位类说明应在上层（metaPrefix/封装备注）统一处理
