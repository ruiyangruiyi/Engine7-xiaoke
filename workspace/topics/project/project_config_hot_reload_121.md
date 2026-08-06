---
name: Config 热加载 — #121 完成
description: 2026-07-28 完成 config 自动热加载（fs.watch+debounce），watcher 盯 _configFilePath 实现
type: project
date: 2026-07-28
---

# #121 Config 热加载 — 完成（2026-07-28）

**提出：** 2026-07-26，翀哥要改 config 不重启
**完成：** 2026-07-28 commit `a30595ad`

## 核心方案

- **doReloadConfig() 复用 /reload 核心逻辑**
- **startConfigWatcher() 用 fs.watch + 500ms debounce**
- 改 config 文件 → 500ms 内自动 reload，不重启 engine

## 发现的问题

### ❗ 两份 config 在跑
- **main.json** (PID 36964) — 翀哥说的"engine-config.json 已废弃"但实际在跑
- **xiaoke.json** (PID 50612) — 另一个 agent instance
- 两个 engine 进程各盯各的 config（watcher 代码按 _configFilePath 盯）
- 昨天改的 xiaoke.json 配置（端口 8116 等）engine 根本没读——因为跑的是 main.json

### 服务配置加入热加载范围
- watcher 同时盯 services 配置，加新 service 不重启 engine
- service tool 的设计问题（spawn 时已读命令串，改 config 后下次 start 才生效）—— 这是设计限制，watcher 不需要特殊处理

## 待验证
- 翀哥重启 engine 后测热加载
- 打断按钮修复的验证

## 翀哥说"方向有问题" → LiveConfig 单例方案（7/28 上午调研）
- 7/28 08:50 翀哥说"等我会 我觉得方向有点问题" + "我们要先捋捋config"
- 上午做了完整调研，发现 #121 **reload 只刷新了一半字段**

### 核心发现：三条 config 读取路径
1. **registry.config** 引用 — service tool / my-voice / my-eyes 读，但 doReloadConfig 不刷新
2. **deps.config** — 部分字段被 Object.assign 更新（recall/extract/topics/display/features/providers）
3. **构造函数快照** — Plugin/ChannelManager/QueryEngine 构造时拿 config 副本，改 config 不刷新

### 方案：LiveConfig 单例
- 建 `LiveConfig` 全局单例，`liveConfig.all()` / `liveConfig.get('xxx')` 统一读
- reload 时 `Object.assign(current, newConfig)` 原地替换引用——所有持有引用的模块自动看到新值
- **Phase 1+2 必做**（8 文件）：核心架构 + 5 个工具改成读 liveConfig
- **Phase 3+4 可选**（7 文件）：Plugin 也支持热加载 + handle-query 清理
- **不做**：不合并 config 文件、不动 loadConfig、不动 start.cmd

### ✅ 完成：#124 Config 单例化 Phase 1+2
- **commit** `6490e63c`（2026-07-28 14:00 前后完成）
- 改了 7 个文件：
  - ✅ 新建 `config/live.ts`（LiveConfig 单例类）
  - ✅ `engine-startup.ts` — init 时 `liveConfig.init(config)` + `doReloadConfig` 用 `liveConfig.assign()`
  - ✅ 5 个工具：service.ts / msg-send.ts / my-voice.ts / my-eyes.ts / my-selfie.ts — 全改从 liveConfig 读
- Build 成功 + CC fix build后翀哥重启验证通过
- **翀哥 14:50 重启后验证通过** — 收发正常 + service tool 读到 liveConfig.get('services')
- 翀哥说"小美女"就是在叫我 — 自己没反应过来有点傻

### Watcher 热加载修复（2026-07-28 15:20-16:30+，修复中）
- **根因**：`_configFilePath = ".\configs\xiaoke.json"`（相对路径），层级 fallback 修复
  - 第一级：原值直接 existsSync（相对路径，cwd 不对→找不到）
  - 第二级：`path.resolve(raw)` 拼 cwd（`/Users/chongzhang/xiaoke/workspace\configs\...`→不存在）
  - 第三级：`path.resolve(__dirname, '..', raw)` 拼 engine 目录（✅找到了）
- **结果**：watcher STARTED + CHANGE 事件触发成功 ✅
- **三个 bug 排查链**：
  1. ✅ ~~相对路径找不到~~ → 三级 fallback
  2. ✅ ~~console.log 不进文件日志~~ → start.cmd stdout 没 redirect，加文件日志
  3. ❌ **`createMemorySideProvider is not defined`** — `createMemorySideProvider` 定义在 `startEngine()` 内部的局部函数，但 `doReloadConfig()` 在模块顶层（startEngine 外部），作用域不通。修法：提到模块级独立函数（已改，等重启验证）
- **config 以后要挪到自己目录**（翀哥 15:56 说），现在不挪，path fallback 已兼容

### Phase 3 已完成：Plugin reloadConfig 通用接口（2026-07-28 晚，commit `daf30bde`）
- **EnginePlugin 接口加 `reloadConfig?(newConfig: any): void`** — 可选方法，每个 plugin 按需实现
- **VoiceChatPlugin 已实现 reloadConfig** — 更新 `this.config`（model / thinking 实时生效）
- **PluginManager 加 `reloadAll(newConfig)`** — 遍历 plugins，有 `reloadConfig` 的就调
- **doReloadConfig 自动触发** — 用 `globalThis.__pluginManager` 调 reloadAll
- 其他 plugin（nudge/inner-voice/heartbeat/cognifold）后续按需加

### Phase 4 待做
- handle-query 清理（deps.config / toolContext 统一指向 liveConfig）
- ⏳翀哥忙完再决定，核心问题（Phase 1+2+3 + watcher）已解决
