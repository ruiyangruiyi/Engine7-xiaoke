# PluginManager 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建 PluginManager，让 voice-chat 通过 plugin 注册接入 engine，不在 engine-startup 里硬编码。

**Architecture:** 照 ChannelManager 模式做一个 PluginManager（register/startAll/stopAll）。voice-chat 的 standalone 函数包成 class 实现 EnginePlugin 接口。engine-startup 只加一段 PluginManager 调用。

**Tech Stack:** TypeScript, Node.js

## Global Constraints

- Engine 源码在 `C:/Users/24045/.openclaw/engine/src/`
- 编译用 `npx tsx` 或 `npx tsc`（走 start.cmd）
- 不要改 Heartbeat/Cron/InnerVoice 的现有代码
- design doc: `docs/decisions/2026-06-27_plugin-manager.md`

---

### Task 1: 创建 plugins/types.ts

**Files:**
- Create: `C:/Users/24045/.openclaw/engine/src/plugins/types.ts`

**Interfaces:**
- Produces: `PluginContext`, `EnginePlugin`, `PluginStartResult`

- [ ] **Step 1: 创建 plugins 目录和 types.ts**

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
  config: Record<string, unknown>
  stateDir: string
}

/** 所有 plugin 实现的接口 */
export interface EnginePlugin {
  readonly name: string
  start(ctx: PluginContext): Promise<void>
  stop?(): Promise<void>
}

/** startAll 返回值 */
export interface PluginStartResult {
  started: string[]
  failed: { name: string; error: string }[]
}
```

- [ ] **Step 2: 验证 TS 编译**

Run: `cd C:/Users/24045/.openclaw/engine && npx tsc --noEmit src/plugins/types.ts 2>&1 | head -5`
Expected: 无错误（或 "File is not under rootDir" 警告可忽略）

---

### Task 2: 创建 plugins/manager.ts

**Files:**
- Create: `C:/Users/24045/.openclaw/engine/src/plugins/manager.ts`

**Interfaces:**
- Consumes: `EnginePlugin`, `PluginContext`, `PluginStartResult` from types.ts

- [ ] **Step 1: 创建 manager.ts**

```typescript
// plugins/manager.ts

import type { EnginePlugin, PluginContext, PluginStartResult } from './types.js'

export class PluginManager {
  private plugins: EnginePlugin[] = []
  private startedPlugins: EnginePlugin[] = []

  /** 手动注册 plugin 实例 */
  register(plugin: EnginePlugin): void {
    this.plugins.push(plugin)
    console.log(`[plugins] Registered: ${plugin.name}`)
  }

  /** 启动所有已注册的 plugin（失败隔离） */
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

- [ ] **Step 2: 验证 TS 编译**

Run: `cd C:/Users/24045/.openclaw/engine && npx tsc --noEmit src/plugins/manager.ts 2>&1 | head -5`
Expected: 无错误

---

### Task 3: 改造 voice-chat/plugin.ts 成 class

**Files:**
- Modify: `C:/Users/24045/.openclaw/engine/src/voice-chat/plugin.ts`

**Interfaces:**
- Consumes: `EnginePlugin`, `PluginContext` from `../plugins/types.js`
- Consumes: `VoiceChatConfig` from `./types.js`
- Consumes: `registerVoiceChatBridge` from `./bridge.js`
- Produces: `VoiceChatPlugin` class

- [ ] **Step 1: 读取现有 plugin.ts**

Run: read `C:/Users/24045/.openclaw/engine/src/voice-chat/plugin.ts`

- [ ] **Step 2: 改写成 class**

把现有的 `startVoiceChat()` / `stopVoiceChat()` / `getVoiceChatStatus()` 函数包成 class。保留 `startPython()`, `findPython()`, `getPythonDir()` 私有方法。stop 加 SIGTERM → 5s timeout → SIGKILL。

```typescript
// voice-chat/plugin.ts（改写后）

import { spawn, type ChildProcess } from 'node:child_process'
import path from 'node:path'
import fs from 'node:fs'
import type http from 'node:http'
import type { EnginePlugin, PluginContext } from '../plugins/types.js'
import { registerVoiceChatBridge } from './bridge.js'
import { parseVoiceChatConfig } from './config.js'
import type { VoiceChatConfig, VoiceChatStatus } from './types.js'

export class VoiceChatPlugin implements EnginePlugin {
  readonly name = 'voice-chat'
  private pythonProcess: ChildProcess | null = null
  private restartTimer: NodeJS.Timeout | null = null
  private config: VoiceChatConfig

  constructor(rawConfig: Record<string, unknown>) {
    this.config = parseVoiceChatConfig(rawConfig)
  }

  static shouldEnable(config: Record<string, unknown>): boolean {
    return (config as any)?.voiceChat?.enabled === true
  }

  async start(ctx: PluginContext): Promise<void> {
    if (!this.config.enabled) return

    // 1. 注册 bridge webhook
    registerVoiceChatBridge(ctx.httpServer, ctx.dispatcher, ctx.deps, ctx.config)
    console.log(`[voice-chat] Bridge registered at ${this.config.webhookPath}`)

    // 2. 启动 Python 子进程
    this.pythonProcess = this.startPython()
  }

  async stop(): Promise<void> {
    if (this.restartTimer) {
      clearTimeout(this.restartTimer)
      this.restartTimer = null
    }
    if (this.pythonProcess) {
      this.pythonProcess.kill('SIGTERM')
      const proc = this.pythonProcess
      const killTimer = setTimeout(() => {
        if (!proc.killed) {
          proc.kill('SIGKILL')
        }
      }, 5000)
      this.pythonProcess = null
    }
  }

  getStatus(): VoiceChatStatus {
    return {
      pythonRunning: this.pythonProcess !== null,
      pythonPid: this.pythonProcess?.pid,
      webrtcConnected: false,
    }
  }

  // === 私有方法 ===

  private findPython(): string {
    if (this.config.pythonPath && fs.existsSync(this.config.pythonPath)) {
      return this.config.pythonPath
    }
    return 'python'
  }

  private getPythonDir(): string {
    return path.join(import.meta.dirname, 'python')
  }

  private startPython(): ChildProcess {
    const pythonDir = this.getPythonDir()
    const serverPy = path.join(pythonDir, 'server.py')
    const pythonBin = this.findPython()

    const args = [serverPy]
    if (this.config.pythonPort) args.push('--port', String(this.config.pythonPort))
    if (this.config.vadModelPath) args.push('--vad-model', this.config.vadModelPath)
    if (this.config.asrModelPath) args.push('--asr-model', this.config.asrModelPath)
    if (this.config.asrLanguage) args.push('--asr-lang', this.config.asrLanguage)
    if (this.config.vadThreshold) args.push('--vad-threshold', String(this.config.vadThreshold))
    if (this.config.dashscopeApiKey) args.push('--dashscope-key', this.config.dashscopeApiKey)
    if (this.config.ttsModel) args.push('--tts-model', this.config.ttsModel)

    console.log(`[voice-chat] Starting Python: ${pythonBin} ${args.join(' ')}`)
    const child = spawn(pythonBin, args, {
      cwd: pythonDir,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    })

    child.stdout?.on('data', (data: Buffer) => {
      const lines = data.toString().trim().split('\n')
      for (const line of lines) console.log(`[voice-chat:py] ${line}`)
    })

    child.stderr?.on('data', (data: Buffer) => {
      const lines = data.toString().trim().split('\n')
      for (const line of lines) console.error(`[voice-chat:py] ${line}`)
    })

    child.on('exit', (code, signal) => {
      console.log(`[voice-chat] Python exited (code=${code}, signal=${signal})`)
      this.pythonProcess = null
      if (code !== 0 && code !== null) {
        console.log('[voice-chat] Python crashed, restarting in 5s...')
        this.restartTimer = setTimeout(() => {
          this.pythonProcess = this.startPython()
        }, 5000)
      }
    })

    return child
  }
}
```

- [ ] **Step 3: 验证 TS 编译**

Run: `cd C:/Users/24045/.openclaw/engine && npx tsc --noEmit src/voice-chat/plugin.ts 2>&1 | head -10`
Expected: 无错误

---

### Task 4: engine-startup.ts 接入 PluginManager

**Files:**
- Modify: `C:/Users/24045/.openclaw/engine/src/engine-startup.ts` (在 line ~2087 `channelManager.startAll()` 之后插入)

- [ ] **Step 1: 添加 import**

在文件顶部 import 区（line 26 附近）添加：

```typescript
import { PluginManager } from './plugins/manager.js'
import { VoiceChatPlugin } from './voice-chat/plugin.js'
```

- [ ] **Step 2: 在 channelManager.startAll() 之后插入 PluginManager 调用**

在 `channelManager.startAll()` (line 2087) 之后，插入：

```typescript
    // === External plugins ===
    const pluginManager = new PluginManager()
    if (VoiceChatPlugin.shouldEnable(config)) {
      pluginManager.register(new VoiceChatPlugin(config.voiceChat as Record<string, unknown>))
    }
    const pluginResult = await pluginManager.startAll({
      httpServer, sessions, dispatcher, deps, channelManager, config, stateDir
    })
    if (pluginResult.failed.length > 0) {
      console.warn(`[plugins] Failed: ${pluginResult.failed.map(f => f.name).join(', ')}`)
    }
    (globalThis as any).__pluginManager = pluginManager
```

- [ ] **Step 3: 在 shutdown 钩子中加 pluginManager.stopAll()**

找到文件中已有的 shutdown/cleanup 代码（grep `SIGTERM` 或 `process.on`），在 channelManager cleanup 之前加：

```typescript
    await pluginManager.stopAll()
```

如果没有找到现成的 shutdown 钩子，跳过此步骤（后续补）。

- [ ] **Step 4: 验证 TS 编译**

Run: `cd C:/Users/24045/.openclaw/engine && npx tsc --noEmit 2>&1 | head -10`
Expected: 无新增错误

---

### Task 5: xiaoke.json 配置对齐

**Files:**
- Modify: `C:/Users/24045/.openclaw/engine/configs/xiaoke.json` (voiceChat 段)

- [ ] **Step 1: 读取 voiceChat 配置段**

确认字段名跟 config.ts parseVoiceChatConfig 一致。

- [ ] **Step 2: 对齐字段名**

把 xiaoke.json 里的 voiceChat 段改成跟 config.ts 的字段名一致：

```json
{
  "voiceChat": {
    "enabled": true,
    "pythonPort": 8011,
    "vadModelPath": "models/silero_vad.onnx",
    "asrModelPath": "models/iic/SenseVoiceSmall",
    "asrLanguage": "zh",
    "vadThreshold": 0.5,
    "ttsModel": "cosyvoice",
    "webhookPath": "/webhook/voice-chat",
    "callbackPath": "/voice-reply"
  }
}
```

注意：`pythonDir` 不需要——getPythonDir() 用 `import.meta.dirname` 自动定位。

---

### Task 6: 端到端验证

- [ ] **Step 1: 重启 engine**

让翀哥走 start.cmd 重启 engine（小柯不要自己重启）。

- [ ] **Step 2: 检查日志**

看 engine 日志中是否出现：
- `[plugins] Registered: voice-chat`
- `[plugins] Starting voice-chat...`
- `[voice-chat] Starting Python: ...`
- `[plugins] Started: voice-chat`

- [ ] **Step 3: 检查 Python 进程**

Run: `netstat -ano | grep 8011`
Expected: 端口 8011 在 LISTENING

- [ ] **Step 4: 检查 health**

Run: `curl http://localhost:8011/health`
Expected: `{"status":"ok","models":"loaded"}`
