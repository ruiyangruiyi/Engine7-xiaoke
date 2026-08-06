# Engine Config 单例化重构方案

**日期**: 2026-07-28
**目标**: 统一 config 读取入口，reload 时全局生效
**起因**: 翀哥说"config 节点管理很乱"，调研发现三条读取路径 + reload 覆盖不全

---

## 问题

当前 config 读取有 3 条路径，reload 覆盖不全：

| 路径 | 使用方 | reload 是否刷新 |
|---|---|---|
| `registry.config` | service / msg-send / my-voice（动态读） | ❌ 不刷新 |
| `deps.config` | handle-query / my-eyes / my-selfie（动态读） | ✅ 部分（Object.assign 原地改的字段） |
| 闭包 config | startEngine 内部 + 各 Plugin 构造函数快照 | ❌ Plugin 不刷新 |

**痛点**：改 `config.services.voice-chat.start` 后，service tool 仍读老命令（registry.config 没换）。

---

## 方案：LiveConfig 全局可变单例

### 核心：一个可变对象 + 统一读取入口

```ts
// config/live.ts
class LiveConfig {
  private current: EngineConfig

  init(config: EngineConfig) {
    this.current = config
  }

  all(): EngineConfig {
    return this.current
  }

  get<T = any>(path: string): T | undefined {
    return path.split('.').reduce((acc, key) => acc?.[key], this.current as any)
  }

  async reload(): Promise<{ changes: string[] }> {
    const newConfig = loadConfig(this.current._configFilePath)
    Object.assign(this.current, newConfig)  // 原地替换
    return { changes: [...] }
  }
}
export const liveConfig = new LiveConfig()
```

### 关键：Object.assign 是原地改

不换引用，只改字段值。所有持有 `this.current` 引用的模块自动看到新字段值。

---

## 改动分四个 Phase

### Phase 1：核心架构（必做）

| 文件 | 改动 |
|---|---|
| `config/live.ts` | **新建**：LiveConfig 类 + `liveConfig` 单例 |
| `engine-startup.ts` | `registry.config = config` → `liveConfig.init(config)`；deps.config 指向 `liveConfig.all()`；`doReloadConfig()` 简化为 `Object.assign(current, newConfig)` |

### Phase 2：工具层（让动态读的工具立刻生效，必做）

| 文件 | 改动 |
|---|---|
| `tools/service.ts` | `registry.config?.services` → `liveConfig.get('services')` |
| `tools/msg-send.ts` | `registry.config` → `liveConfig.all()` |
| `tools/my-voice.ts` | `registry.config?.tools?.my_voice` → `liveConfig.get('tools.my_voice')` |
| `tools/my-eyes.ts` | `(ctx as any).config?.tools?.my_eyes` → `liveConfig.get('tools.my_eyes')` |
| `tools/my-selfie.ts` | `(ctx.config as any)` → `liveConfig.all()` |

### Phase 3：Plugin 层（让 Plugin 也响应 reload，可选）

| 文件 | 改动 |
|---|---|
| `nudge/plugin.ts` | 构造函数参数接 liveConfig，运行时 `liveConfig.get('nudge.xxx')` |
| `inner-voice/plugin.ts` | 同上 |
| `heartbeat.ts` | 同上 |
| `voice-chat/plugin.ts` | 同上（voiceChat 段） |
| `memory/cognifold/plugin.ts` | 同上（cognifold 段） |

### Phase 4：handle-query 简化（清理，可选）

`deps.config` / `toolContext.config` 都指向 `liveConfig.all()`

---

## 不做的事

- 不动 loadConfig()：保持纯函数
- 不动两个 config 文件（main.json / xiaoke.json）：两份独立 config 不合并
- 不动 start.cmd：启动流程不变
- 不引入 subscribe/observable：保持简单，reload 就 Object.assign

---

## 风险

1. **Object.assign 浅拷贝**：嵌套对象整个替换。读法 `current.services.voice-chat` 每次动态访问，没问题。禁止缓存引用。
2. **Plugin 构造快照**：不做 Phase 3 的话，Plugin 不支持热加载（老限制，没变差）。
3. **reload 期间正在执行的 handler**：JS 单线程无并发，Object.assign 同步完成。

---

## 验证

- 改 `config.services.voice-chat.start` → service tool 立刻用新命令
- 改 `config.tools.my_voice.provider` → my-voice 立刻用新 provider
- 改 `config.topics.recall.model` → recall 立刻切模型

---

## 工作量

- Phase 1+2（必做）：8 文件
- Phase 3+4（可选）：7 文件
