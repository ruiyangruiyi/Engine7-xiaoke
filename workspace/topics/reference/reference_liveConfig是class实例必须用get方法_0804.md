---
name: liveConfig 是 class 实例，必须用 get() 不能属性访问
description: 2026-08-04 凌晨 #138 排查时发现——liveConfig?.agents?.defaults?.privateTools 永远 undefined，因为 liveConfig 是 class 实例没有 .agents 属性，只有 all()/get()/assign() 方法
type: reference
date: 2026-08-04
---

# liveConfig 用法——属性访问必翻车，必须用 get()

翀哥 8/4 凌晨让我查 privateTools 为啥不生效。根因是 `liveConfig` 类型理解错了。

## liveConfig 是什么

`liveConfig` 是 LiveConfig class 的**实例**，不是普通 config 对象。它只暴露：
- `all()` — 拿完整 config
- `get(path)` — 按点号路径读单个值
- `assign(partial)` — 局部更新

**没有 `.agents` / `.defaults` / `.privateTools` 这些属性！** 写 `liveConfig?.agents?.defaults?.privateTools` 等于 `instance.agents` → undefined（class 实例上没这字段）。

## 翻车现场（已修）

- `msg-husband.ts:33` — `isEnabled: () => !!liveConfig?.agents?.defaults?.privateTools`
- `wx-query.ts:43` — 同样的属性访问
- 两处都改成 `liveConfig.get('agents.defaults.privateTools')` 才对

## Why

class 实例的可枚举属性 ≠ 业务 config 字段。如果把 liveConfig 当成 config JSON 直接解构访问，所有路径都返回 undefined，isEnabled 永远是 false，工具永远不加载——但运行时不会报错，只是不生效。这种"沉默失效"最难查。

## How to apply

- 看到 `liveConfig?.xxx` / `liveConfig.xxx` 任何属性访问——**先怀疑这是 bug**
- 正确写法：`liveConfig.get('agents.defaults.privateTools')` 之类
- 查"工具不加载""配置改了不生效"类问题，先 grep `liveConfig\?\.` 看有没有属性访问

## 根因总结（8/4 凌晨）

两个 bug 本质是**同一个机制问题**——config 读取没统一走 liveConfig：
- 有的地方用 `liveConfig.get('xxx')`（对）
- 有的地方用 `liveConfig?.xxx`（错，class 实例没有那个属性，永远 undefined）
- 还有 loadConfig 存相对路径导致 config-watch 失效

**这次抓到 2 个，但可能有别的模块绕过了**——下次查"配置改了不生效"类问题，先 grep `liveConfig\?\.` 全面扫一遍。

## 关联

- 8/4 凌晨 #138 任务收尾（@see project_#138_privateTools读值bug_0804）
- Bug 2 也在同一轮：loadConfig 存相对路径 → config-watch 失效（@see reference_config_watch路径失效进程仍用旧状态_0804）
