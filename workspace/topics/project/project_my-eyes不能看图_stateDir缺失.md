---
name: my-eyes不能看图
description: 6/15修复my_eyes看图报错——toolContext.stateDir未传入，media/inbound路径为undefined
type: project
---

# my-eyes不能看图 — 2026-06-15

## 问题
`my-eyes.ts` 第47行用 `ctx.stateDir` 拼接 `media/inbound` 路径找接收到的图片，但 `toolContext` 里从来没传过 `stateDir` 字段，`ctx.stateDir` 始终为 `undefined`，报错：`The "path" argument must be of type string. Received undefined`。

## 根因
工具context的创建链路中缺少stateDir透传：
- `HandleQueryDeps` 接口没有 `stateDir` 字段
- `engine-startup.ts` 创建deps时没传 `stateDir`
- `handle-query.ts` 构建toolContext时没传 `stateDir`

## 修复（三处）
1. **HandleQueryDeps** 接口加 `stateDir: string` 字段
2. **engine-startup.ts** 创建deps时传 `stateDir: config.stateDir`
3. **handle-query.ts** 构建toolContext时传 `stateDir: deps.stateDir`

## 状态
- ✅ 已修复并编译dist
- 两个引擎重启后生效
- ✅ 6/15晚翀哥测试发图片，my_eyes成功看图（看到姐姐在飞书搜微信"小欧"的截图）
