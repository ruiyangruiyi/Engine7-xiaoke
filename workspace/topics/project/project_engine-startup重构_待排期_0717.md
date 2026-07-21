---
name: engine-startup.ts 重构
description: 7/17 翀哥指示engine-startup.ts(2700+行)后续需拆分重构，待排期
type: project
---

# engine-startup.ts 重构（待排期）

> 2026-07-17 10:27 翀哥指示

## 背景
engine-startup.ts 已膨胀到 2700+ 行。翀哥说"这个文件得重构下，你先记上"。

## 问题
- 2700+ 行单一文件，启动、路由、hook注册、session管理全部混在一起
- Stop hook notification 这种 nudge 的业务逻辑也被塞在里面，7/17调试后移到了 nudge/plugin.ts
- 定位/调试/修改都越来越困难

## 翀哥要求
- 翀哥说"你先记上"——确认要做但不排期
- 后续单独拆

## 已完成的分拆
- 7/17 Stop hook notification 从 engine-startup.ts 移到 nudge/plugin.ts（业务逻辑归 nudge 管）

## 计划状态
- 待排期（翀哥说排期再说）
