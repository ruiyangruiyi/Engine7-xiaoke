# PluginManager 架构设计

> 作者：小柯  
> 日期：2026-06-27  
> 状态：已 review（姐姐），按反馈修订 v2

## 背景

Engine 现在有 3 个"内部 plugin"（Heartbeat、InnerVoice、Cron）和 1 个新的外部 plugin（VoiceChat）。它们的生命周期管理全部 ad-hoc 散落在 `engine-startup.ts`（2545 行）里：

```typescript
// 现状：每个 plugin 各写一段
if (config.heartbeat?.enabled && HeartbeatPlugin.shouldEnable(...)) {
  const heartbeat = new HeartbeatPlugin(config.heartbeat, sessions)
  heartbeat.start(sessions, deps, dispatcher)
}

if (config.cron?.enabled) {
  const cronPlugin = new CronPlugin(config.cron, ...)
  await cronPlugin.start()
}

// voice-chat 也打算这么写… 但不能再堆了
```

**问题**：
1. engine-startup.ts 已经 2545 行，每加一个 plugin 就更胖
2. 没有统一的 Plugin 接口——每个 plugin 的 constructor 签名、start 参数都不同
3. 没有 fail isolation——一个 plugin start 失败可能影响其他
4. 新 plugin 接入成本高，要改 engine-startup 多处

## 目标

- voice-chat 不在 engine-startup 里硬编码调用
- 以后新 plugin（autoDream、OAC 数字人等）注册一行就能接入
- 跟 ChannelManager 对称，降低理解成本

## 非目标

- **不重写现有的 Heartbeat/Cron/InnerVoice**——先让 voice-chat 走新架构，老 plugin 后续逐步迁移
- 不做动态加载（不需要运行时热插拔）
- 不做插件市场/发现机制（编译期注册就够）

---

## 架构

### 文件结构

```
engine/src/
├── plugins/
│   ├── types.ts          # EnginePlugin 接口 + PluginContext
│   └── manager.ts        # PluginManager（注册/启动/停止）
├── voice-chat/
│   ├── plugin.ts         # VoiceChatPlugin implements EnginePlugin
│   ├── bridge.ts         # （不变）
│   ├── config.ts         # （不变）
│   └── python/           # （不变）
├── heartbeat.ts          # （暂不动，后续迁移）
├── cron/cron-plugin.ts   # （暂不动）
└── engine-startup.ts     # 只加一段 PluginManager 调用
```

### EnginePlugin 接口

```typescript
// plugins/types.ts

import type http from 'node:http'
import type { SessionManager } from '../session/session-manager.js'
import type { MessageDispatcher } from '../core/message-dispatcher.js'
import type { HandleQueryDeps } from '../handle-query.js'
import type { ChannelManager } from '../channels/manager.js'

/** Plugin 启动时拿到的上下文 */
export interface PluginContext {
  httpServer: http.Server
  sessions: SessionManager
  dispatcher: MessageDispatcher
  deps: HandleQueryDeps
  channelManager: ChannelManager
  config: Record<string, unknown>  // 整个 engine config（各 plugin 读自己需要的段）
  stateDir: string
}

/** 所有 plugin 实现的接口 */
export interface EnginePlugin {
  /** plugin 名称，用于日志和调试 */
  readonly name: string

  /** 启动 plugin（资源初始化、进程 spawn、timer 设置等） */
  start(ctx: PluginContext): Promise<void>

  /** 停止 plugin（清理资源、kill 子进程、清 timer） */
  stop?(): Promise<void>
}
```

### PluginManager

```typescript
// plugins/manager.ts

/** 启动结果 */
export interface PluginStartResult {
  started: string[]
  failed: { name: string; error: string }[]
}

export class PluginManager {
  private plugins: EnginePlugin[] = []
  private startedPlugins: EnginePlugin[] = []

  /** 手动注册 plugin 实例 */
  register(plugin: EnginePlugin): void {
    this.plugins.push(plugin)
    console.log(`[plugins] Registered: ${plugin.name}`)
  }

  /** 启动所有已注册的 plugin（失败隔离：一个挂不影响其他） */
  async startAll(ctx: PluginContext): Promise<PluginStartResult> {
    const started: string[] = []
    const failed: { name: string; error: string }[] = []

    for (const plugin of this.plugins) {
      try {
        console.log(`[plugins] Starting ${plugin.name}...`)
        await plugin.start(ctx)
        this.startedPlugins.push(plugin)
        started.push(plugin.name)
        console.log(`[plugins] Started: ${plugin.name}`)
      } catch (err: any) {
        console.error(`[plugins] Failed to start ${plugin.name}: ${err.message}`)
        failed.push({ name: plugin.name, error: err.message })
        // 不 break，继续启动其他 plugin
      }
    }
    return { started, failed }
  }

  /** 停止所有已启动的 plugin（逆序停止） */
  async stopAll(): Promise<void> {
    for (const plugin of [...this.startedPlugins].reverse()) {
      try {
        await plugin.stop?.()
        console.log(`[plugins] Stopped: ${plugin.name}`)
      } catch (err: any) {
        console.error(`[plugins] Error stopping ${plugin.name}: ${err.message}`)
      }
    }
    this.startedPlugins = []
  }
}
```

### VoiceChatPlugin 改造

现有 `plugin.ts` 的 standalone 函数包成 class：

```typescript
// voice-chat/plugin.ts（改造后）

export class VoiceChatPlugin implements EnginePlugin {
  readonly name = 'voice-chat'
  private pythonProcess: ChildProcess | null = null
  private restartTimer: NodeJS.Timeout | null = null

  constructor(private config: VoiceChatConfig) {}

  static shouldEnable(config: any): boolean {
    return config?.voiceChat?.enabled === true
  }

  async start(ctx: PluginContext): Promise<void> {
    // 1. 注册 bridge webhook（用 ctx.httpServer, ctx.dispatcher, ctx.deps）
    registerVoiceChatBridge(ctx.httpServer, ctx.dispatcher, ctx.deps, ctx.config)

    // 2. spawn Python 子进程
    this.pythonProcess = this.startPython(ctx)
  }

  async stop(): Promise<void> {
    if (this.restartTimer) clearTimeout(this.restartTimer)
    if (this.pythonProcess) {
      this.pythonProcess.kill('SIGTERM')
      // 5s 后还没退出 → SIGKILL
      setTimeout(() => {
        if (this.pythonProcess && !this.pythonProcess.killed) {
          this.pythonProcess.kill('SIGKILL')
        }
      }, 5000)
      this.pythonProcess = null
    }
  }

  // startPython / findPython 等私有方法不变
}
```

### engine-startup.ts 接入

替换原来散落的 ad-hoc 调用，只加一段：

```typescript
// engine-startup.ts（新增段）

import { PluginManager } from './plugins/manager.js'
import { VoiceChatPlugin } from './voice-chat/plugin.js'

// ... 在 channelManager.startAll() 之后 ...

const pluginManager = new PluginManager()

// 外部 plugin（走新架构）
if (VoiceChatPlugin.shouldEnable(config)) {
  pluginManager.register(new VoiceChatPlugin(config.voiceChat))
}

// 启动
await pluginManager.startAll({
  httpServer, sessions, dispatcher, deps, channelManager, config, stateDir
})

// shutdown 时
process.on('SIGTERM', async () => {
  await pluginManager.stopAll()
})
```

**注意**：Heartbeat / Cron / InnerVoice 暂不迁移——它们继续走现有的 ad-hoc 代码，后续逐步迁移。

---

## 配置格式

xiaoke.json 里 voiceChat 段的字段名需对齐 config.ts：

```json
{
  "voiceChat": {
    "enabled": true,
    "pythonPath": "python",
    "pythonPort": 8011,
    "vadModelPath": "models/silero_vad.onnx",
    "asrModelPath": "models/iic/SenseVoiceSmall",
    "asrLanguage": "zh",
    "vadThreshold": 0.5,
    "dashscopeApiKey": "",
    "ttsModel": "cosyvoice",
    "webhookPath": "/webhook/voice-chat",
    "callbackPath": "/voice-reply"
  }
}
```

---

## 设计决策

### 为什么不做 plugin 自动发现

- Engine 是 TypeScript 编译项目，不是动态加载运行时
- 编译期 import + `pluginManager.register()` 足够
- 自动发现（扫描目录）增加复杂度但没有实际收益

### 为什么 PluginContext 传整个 config

- 每个 plugin 读自己需要的段（voiceChat / heartbeat / cron）
- 避免给 PluginContext 定义 10 个可选字段
- 跟 ChannelManager.loadFromConfig 传整个 channelsConfig 一致

### 为什么先不迁移老 plugin

- 降低风险：voice-chat 是新模块，先验证 PluginManager 能跑通
- 老 plugin 稳定运行中，动了可能引入 bug
- 迁移是 mechanical work，后续可以一把做

### 失败隔离策略

- `startAll` 里 try-catch 每个 plugin
- 一个 plugin start 失败 → log error，继续启动其他
- 不做自动重试（keep it simple）

---

## 验证标准

1. `PluginManager.register()` + `startAll()` 能启动 VoiceChatPlugin
2. VoiceChatPlugin.start() 能 spawn Python server.py
3. Python ASR 文字 → POST webhook → engine 处理 → 回复 → TTS → 浏览器
4. engine-startup.ts 新增代码 < 20 行
5. 一个 plugin start 失败不阻塞其他 plugin

---

## 后续（不在本次范围）

- [ ] Heartbeat 迁移到 PluginManager
- [ ] Cron 迁移到 PluginManager
- [ ] InnerVoice 迁移到 PluginManager
- [ ] engine-startup.ts 瘦身（目标 < 2000 行）
- [ ] Plugin 依赖声明（如 voice-chat 依赖 channelManager）

---

## 修订记录

- **v2（2026-06-27 姐姐 review 后）**：
  1. `config: any` → `config: Record<string, unknown>`（类型收紧）
  2. `startAll` 返回 `{ started, failed }`（调用方可知哪个 plugin 挂了）
  3. stop 加 SIGTERM → 5s timeout → SIGKILL（防 Python 不退出）
  4. 砍掉 registry.ts（YAGNI，现阶段直接 register 实例）
- v1（2026-06-27）：初版
