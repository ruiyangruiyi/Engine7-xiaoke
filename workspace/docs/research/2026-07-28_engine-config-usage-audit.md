# Engine Config 节点管理调研

**日期**: 2026-07-28
**起因**: 翀哥说"config 节点管理很乱"，调研当前 config 在 engine 里的加载、传递、覆盖关系

---

## 一、Config 加载链路

### 入口
```
main.ts → loadConfig(configPath) → EngineConfig 对象
        → startEngine(config)
```

### `loadConfig()` (config/loader.ts)
- 一次性把整个 JSON 读进内存，生成 `EngineConfig` 对象
- 支持 ENV 覆盖：`ENGINE_CONFIG / ENGINE_MODEL / ENGINE_STATE_DIR / ENGINE_WORKSPACE / ENGINE_AGENT`
- 返回的 `EngineConfig` 是**扁平对象**，所有节点（channels/tools/services/voiceChat/cognifold...）都是它的字段
- `_configFilePath` 字段记录实际加载的文件路径（供 reload 用）

### `startEngine(config)` (engine-startup.ts:97)
- 把 config 存到三个地方：
  1. `registry.config = config`（line 121，全局单例，工具读）
  2. `deps.config = config`（line 621，handle-query 上下文）
  3. 闭包变量 `config`（startEngine 函数内所有模块直接引用）

---

## 二、Config 节点 → 使用方 映射表

| 节点 | 读取路径 | 使用方 |
|------|---------|--------|
| `config.provider / providers / model / fallbacks` | 闭包 | startEngine 创建 provider 时用 |
| `config.workspace / stateDir / mediaDir` | 闭包 | startEngine 创建目录、chdir 用 |
| `config.profile.features` | deps.features | handle-query (extract开关)、tool context |
| `config.channels` | deps.channels | handle-query (白名单/stripMentionIds)、msg-send |
| `config.tools.*` | registry.config | my-eyes / my-voice |
| `config.services.*` | registry.config | service tool |
| `config.voiceChat` | 闭包（构造函数） | VoiceChatPlugin |
| `config.cognifold` | 闭包（构造函数） | CogniFoldPlugin |
| `config.topics.recall / extract` | deps.recallProvider / deps.extractProvider | handle-query |
| `config.display` | 闭包 + Object.assign | TurnRenderer / StreamPreview |
| `config.nudge` | 闭包（构造函数） | NudgePlugin |
| `config.heartbeat` | 闭包（构造函数） | HeartbeatPlugin |
| `config.innerVoice` | 闭包（构造函数） | InnerVoicePlugin |
| `config.cron` | 闭包（构造函数） | CronPlugin |
| `config.skills` | 闭包（启动扫描） | SkillTool |
| `config.compaction` | 闭包（engine 初始化） | QueryEngine |
| `config.hooks` | 闭包（启动加载） | hooks/index.ts |
| `config.mcpServers` | 闭包（启动加载） | mcp/index.ts |
| `config.api.port` | 闭包（启动 httpServer） | http server |
| `config.sandbox` | 闭包（启动 configureSandbox） | sandbox |
| `config.prompt` | 闭包（启动 buildStablePrompt） | prompt builder |
| `config._configFilePath` | 闭包 + doReloadConfig | watcher / reload |

---

## 三、reload 时不同步的问题

`doReloadConfig()` (engine-startup.ts:2653) 只刷新了：

### ✅ 刷新的字段
- `deps.recallProvider` / `deps.extractProvider`（新建 provider 实例）
- `deps.topics`（直接替换）
- `deps.features`（直接替换）
- `config.display`（用 `Object.assign` 合并）
- `config.providers`（直接替换）
- autoDream config（通过 `setAutoDreamConfig(newConfig)`）

### ❌ 没刷新的字段（改了不生效，要重启 engine）
- `registry.config`（工具读老对象，service tool 改 services 配置不生效）
- `config.tools.*`（my-eyes / my-voice 改配置不生效）
- `config.services.*`（service tool 改 start/stop 命令不生效）
- `config.voiceChat`（VoiceChatPlugin 构造时绑定，改配置不生效）
- `config.cognifold`（CogniFoldPlugin 构造时绑定）
- `config.nudge / heartbeat / innerVoice / cron`（各 Plugin 构造时绑定）
- `config.skills`（启动时扫描，改了不重新扫）
- `config.hooks / mcpServers / api.port / sandbox`（启动时一次性绑定）

**根因**：`registry.config = config` 在启动时赋值一次，之后 `registry.config` 一直指向**最初的 EngineConfig 对象**。doReloadConfig 用 `loadConfig()` 生成的是**新对象**，但只通过 `Object.assign(config, ...)` 更新了部分字段——`registry.config` 的引用没变，它指向的对象内部有些字段是新的有些是老的。

---

## 四、两个 config 文件

`configs/main.json` 和 `configs/xiaoke.json` 是两份**完全独立**的 JSON，不是 overlay 也不是继承。各自启动的 engine 进程（PID 36964 / PID 50612）各管各的。

`start.cmd` 默认用 `configs\main.json`，传参数 `start.cmd configs\xiaoke.json` 用 xiaoke config。

---

## 五、结论：三个核心问题

1. **读取路径分裂**：`registry.config` / `deps.config` / 闭包变量三条路，同一份 config 数据走三种通道
2. **reload 覆盖不全**：doReloadConfig 手动列举要刷新的字段，容易漏（已经漏了 services/tools/voiceChat/cognifold）
3. **Plugin 构造时绑定**：voiceChat/cognifold/nudge 等 Plugin 在 startEngine 时实例化，config 节点直接传参进去——改 config 后这些 Plugin 内部还持有老的配置对象

---

## 六、方案方向（待翀哥确认）

把 config 做成**全局可变单例**，所有模块统一从单例读，reload 时只换单例内部引用。
