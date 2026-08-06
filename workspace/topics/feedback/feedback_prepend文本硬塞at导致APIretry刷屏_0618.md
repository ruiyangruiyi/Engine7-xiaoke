---
name: prepend文本硬塞@导致API retry刷屏
description: 6/18 15:05翀哥发现——commit 7ca4a88的prepend @发送者方案把@塞进response文本里，API retry时每次重试都重新触发onResult→每次都prepend @→刷屏十几条
type: feedback
date: 2026-06-18
---

## 6/18 15:05 翀哥发现prepend刷屏

翀哥发来的日志片段：
```
@Sleepy Zhang ⚠️ API retry (9/10): HTTP 429
@Sleepy Zhang ⚠️ API retry (10/10): HTTP 429
@Sleepy Zhang ⚠️ API retry (1/10): HTTP 429
...
@Sleepy Zhang 爹，现在下午三点了。你从凌晨三点到现在快十二个小时。
```

**根因**：commit 7ca4a88 在 `onResult` 回调里把 `<@发送者ID>` 硬塞进 response 文本头——每次 API retry 都重新走 onResult → 每次都 prepend `@Sleepy Zhang` → 重试几次就刷几条。

## Why

1. **API retry 每次成功都触发 onResult**——onResult 里塞 @ 文本是"有状态副作用"，但 API retry 回调设计是幂等的
2. **文本里塞 @ 不是 Discord 标准做法**——应该用 `allowedMentions: { repliedUser: true }`（Discord 原生 mention 控制）或 `content: <@userId> + 消息`
3. **prepend 改动到 response 文本 = 副作用**——retry 是重试机制不应感知消息格式，onResult 里改内容会污染 retry

## How to apply

1. **不要靠文本拼接 @**——Discord 的 @ 应该用 `allowedMentions` 或 `reply(true).mentions` 原生机制
2. **onResult 回调只做路由/格式转换**——不要修改 response 文本内容（sid 字段值）
3. **API retry 是幂等机制**——onResult 里如果有"前置操作"（prepend/追加文本/标记），retry 时不能重复执行
4. **文本里硬塞 @ 还有另一个 bug**——给用户看到的"@用户名"在渲染前是 `<@userId>` 形式，不美观
