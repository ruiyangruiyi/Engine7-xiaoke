# config 读取审计 — 2026-08-04

## 已修复的 Bug（commit 83bc0628）

### Bug 1: liveConfig 属性访问（已修）
- `msg-husband.ts:33` 和 `wx-query.ts:43` 用 `liveConfig?.agents?.defaults?.privateTools`
- liveConfig 是 class 实例（LiveConfigClass），只有 `all()`/`get()`/`assign()` 方法
- 属性访问永远返回 undefined → isEnabled gate 永远 false
- **修法**: 改成 `liveConfig.get<boolean>('agents.defaults.privateTools')`

### Bug 2: loadConfig 相对路径（已修）
- `config/loader.ts:344` 存相对路径到 `_configFilePath`
- engine 启动后 `chdir(workspace)` 改了 cwd
- config-watch 拿相对路径 `fs.existsSync` 失败 → watcher disabled
- **修法**: `loadConfig()` 里 `path.resolve()` 成绝对路径

## 审计结果：其他模块的 config 访问

### ✅ 正确用法（liveConfig.all() 或 liveConfig.get()）
- `msg-send.ts:17` → `liveConfig.all()`
- `my-eyes.ts:45` → `liveConfig.get('tools.my_eyes.model')`
- `my-selfie.ts:28,38,44` → `liveConfig.all()`
- `my-voice.ts:170` → `liveConfig.get('tools.my_voice')`
- `memory-bridge.ts:127` → `liveConfig.all()`
- `service.ts:26` → `liveConfig.get('services')`
- `wx-query.ts:43` → `liveConfig.get('agents.defaults.privateTools')`（已修）

### ⚠️ 通过 deps/registry 引用（依赖 Object.assign 原地更新）
- `handle-query.ts:467` → `config: (deps as any).config` — 传给 ToolUseContext
- `engine-startup.ts:125` → `registry.config = config`
- 这些是**同一个对象引用**，liveConfig.assign() 做 Object.assign 后自动生效

### ✅ 闭包捕获的 config（启动时绑定，reload 时通过引用更新）
- `cron/scheduler.ts` → `deps.config.tickIntervalMs` 等
- `nudge/` → 不直接读 config（通过 deps 传入）
- `channels/` → 不直接读 config
- `compact/` → 不直接读 config

### 结论
- **只有 msg-husband 和 wx-query 两个文件有 bug（已修）**
- 其他模块都正确使用 liveConfig.all()/get() 或通过 deps 引用
- reload 机制本身设计正确（Object.assign 原地更新），只是个别文件访问方式写错了

## 未解决问题
- Mac 上 esbuild 跑不了，dist 只能手动补丁
- Docker Hub 被墙，无法拉 node:22 镜像做 Docker build
- config-watch 在 Mac 上需要重启 engine 才验证修复
