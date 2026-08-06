# Engine Config 热加载 — 完整落盘

**日期**: 2026-07-28
**状态**: ✅ 已验证通过
**calendar**: #121 (热加载) + #124 (单例化)
**相关 commits**: `a30595ad` → `6490e63c` → `2376a42d` → `a3f68ac4` → `9e4b33ea` → `daf30bde`

---

## 一、做了什么

从"改 config 要重启 engine"到"改 config → 500ms 自动 reload → 所有模块立刻生效"。

### 能力清单

| 能力 | 支持 | 说明 |
|------|------|------|
| services | ✅ 热加载 | service tool 立刻读到新 service |
| tools.my_voice / my_eyes / my_selfie | ✅ 热加载 | 从 liveConfig 读 |
| topics (recall/extract provider) | ✅ 热加载 | 重建 provider 实例 |
| autoDream | ✅ 热加载 | setAutoDreamConfig |
| features | ✅ 热加载 | deps.features 刷新 |
| Plugin (voice-chat) | ✅ 热加载 | reloadConfig 接口 |
| api.port | ❌ 不支持 | HTTP server 已监听 |
| channels (Discord/Feishu) | ❌ 不支持 | 连接已建立 |
| cron | ❌ 不支持 | 定时器已创建 |

---

## 二、架构设计

### 2.1 LiveConfig 全局单例（`config/live.ts`）

**问题**：config 有三条读取路径，reload 只刷新其中一条：
1. `registry.config` — 工具层用
2. `deps.config` — handle-query 用
3. 闭包捕获 — Plugin 用

**方案**：所有模块统一从 `liveConfig` 读：
```typescript
// config/live.ts
class LiveConfigClass {
  private config: Record<string, any> = {}
  init(config) { Object.assign(this.config, config) }
  all() { return this.config }
  get(path: string) { ... }  // 如 get('services') 或 get('tools.my_voice')
  assign(newConfig) { Object.assign(this.config, newConfig) }  // 原地更新
}
export const liveConfig = new LiveConfigClass()
```

**核心**：`Object.assign(current, newConfig)` 原地更新——所有持有 `liveConfig.all()` 引用的模块自动看到新值，不需要重新获取。

### 2.2 Config Watcher（`engine-startup.ts: startConfigWatcher`）

```typescript
fs.watch(configPath, { persistent: true }, (eventType) => {
  debounceTimer = setTimeout(async () => {
    await doReloadConfig(config, deps, provider)
  }, 500)
})
```

- 盯 `_configFilePath`，改文件 500ms 后触发 reload
- debounce 防抖：连续保存只触发一次

### 2.3 doReloadConfig 热加载链

```
config 文件变更
  → fs.watch 检测 (500ms debounce)
  → doReloadConfig()
    → liveConfig.assign(newConfig)     // 原地 Object.assign
    → createMemorySideProvider()       // recall/extract 重建
    → deps.topics / deps.features 刷新
    → setAutoDreamConfig(newConfig)    // autoDream
    → pluginManager.reloadAll(newConfig) // Plugin 热加载
```

### 2.4 Plugin 热加载接口

```typescript
// plugins/types.ts
interface EnginePlugin {
  name: string
  start(ctx): Promise<void>
  stop?(): Promise<void>
  reloadConfig?(newConfig: any): void  // ← 新增，可选
}
```

PluginManager.reloadAll() 遍历所有 plugin 调 reloadConfig。不实现的自动跳过。

VoiceChatPlugin.reloadConfig：刷新 model/thinking 等字段。端口/spawnPython 变了需要 stop()+start()。

---

## 三、踩过的 Bug（按时间顺序）

### Bug 1: 相对路径 → watcher DISABLED

**现象**：`_configFilePath = ".\configs\xiaoke.json"`，`fs.existsSync` 找不到。
**根因**：loadConfig 存的是相对路径，existsSync 用 cwd（workspace）做基准，但 config 在 engine/configs/ 下。
**修法**：三级 fallback：
```typescript
let configPath = raw                           // 原值
if (!existsSync) configPath = path.resolve(raw) // cwd resolve
if (!existsSync) configPath = resolve(__dirname, '..', raw) // engine 目录
```
**commit**: `2376a42d` + `a3f68ac4`

### Bug 2: console.log 不进日志文件

**现象**：watcher 的 `[config-watch] watching` 日志在 engine 日志文件里找不到。
**根因**：start.cmd 用 `node dist/main.mjs` 启动，stdout/stderr 没 redirect。engine 日志文件由内部 logger 写，console.log 只输出到终端。
**修法**：watcher 里加 `fs.appendFileSync` 写到 `stateDir/logs/engine-config-watch.log`。
**commit**: `fa2e1a4a`

### Bug 3: createMemorySideProvider 作用域

**现象**：reload 报 `createMemorySideProvider is not defined`。
**根因**：这个函数定义在 startEngine() 内部（局部函数），doReloadConfig 是模块顶层函数，作用域不通。
**修法**：提到模块级，startEngine 和 doReloadConfig 都能复用。
**commit**: `9e4b33ea`

---

## 四、文件改动清单

| 文件 | 改动 |
|------|------|
| `config/live.ts` | **新建** LiveConfig 全局单例 |
| `engine-startup.ts` | liveConfig.init + doReloadConfig + startConfigWatcher + createMemorySideProvider 提到模块级 |
| `plugins/types.ts` | EnginePlugin 加 reloadConfig? 可选方法 |
| `plugins/manager.ts` | 加 reloadAll() |
| `voice-chat/plugin.ts` | 实现 reloadConfig |
| `tools/service.ts` | registry.config → liveConfig.get('services') |
| `tools/msg-send.ts` | registry.config → liveConfig.all() |
| `tools/my-voice.ts` | registry.config → liveConfig.get('tools.my_voice') |
| `tools/my-eyes.ts` | ctx.config → liveConfig.get('tools.my_eyes.model') |
| `tools/my-selfie.ts` | ctx.config → liveConfig.all() |

---

## 五、关键认知

1. **Object.assign 原地更新是核心**——不是换引用，是改原对象的内容。所有持有引用的模块自动生效。
2. **console.log ≠ engine 日志**——engine 日志文件由内部 logger 写，console.log 输出到终端（start.cmd 没 redirect）。排查 watcher 问题要加文件日志。
3. **_configFilePath 是相对路径**——以后 config 挪到 `/Users/chongzhang/xiaoke/\xiaoke.json`（绝对路径），第一级 existsSync 直接命中。
4. **Plugin config 快照问题**——Plugin 构造时 `this.config = parseVoiceChatConfig(rawConfig)` 存了快照。reloadConfig 刷新 this.config，但 start() 时创建的 voiceChatDeps（model deps）需要重启才重建。
5. **热加载边界**：数据/配置类全部支持，连接/端口/进程类不支持（启动时一次性绑定）。

---

## 六、验证方法

```bash
# 1. 查看 watcher 状态
cat /Users/chongzhang/xiaoke//logs/engine-config-watch.log

# 2. 改 config 后验证 reload
# 在 xiaoke.json services 里加一个 "reload-test"
# 等 1 秒
tail -3 /Users/chongzhang/xiaoke//logs/engine-config-watch.log
# 应看到: CHANGE → RELOAD DONE: ok=true

# 3. 验证 service tool 读到新值
service status
# 应看到 reload-test 出现在列表里

# 4. 验证完删掉 reload-test，reload 会自动生效
```

---

## 七、后续可做（Phase 3+4，不急）

- **Phase 3**: CogniFoldPlugin 实现 reloadConfig（目前只有 VoiceChatPlugin 实现）
- **Phase 4**: handle-query 里 `deps.config` 统一改读 liveConfig（目前 deps.config 指向同一对象，功能正确但语义不统一）
- **config 外迁**: config 从 engine/configs/ 挪到各自 stateDir（如 /Users/chongzhang/xiaoke//xiaoke.json），代码已兼容绝对路径
