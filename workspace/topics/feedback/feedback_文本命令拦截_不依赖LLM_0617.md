---
name: 文本命令拦截——/model等命令不进LLM管道
description: 6/17发现飞书/微信adapter没有onCommand方法，/model命令被当普通消息送进LLM，欠费时切不了模型。在ChannelManager.handleInbound统一拦截文本命令解决。
type: feedback
---

6/17翀哥重启切到DeepSeek后欠费，想 `/model` 切回GLM切不了——因为DeepSeek provider初始化失败，命令卡住。

**根因分析：**
- Discord 有原生 slash command → `adapter.onCommand` 回调 → 命令直接被拦截
- **飞书/微信 adapter 没有实现 `onCommand` 方法** → `/model glm-5.1` 被当普通消息 → 送进 LLM 管道 → LLM 欠费/限流 → 切不了
- 之前以为是 Engine 侧 provider 初始化导致，实际是**消息路由问题**——命令根本没到达命令处理器

**Why:** 模型切换不能依赖AI自己切，需要有硬编码的逃生通道。欠费/限流时LLM不可用，但 `/model` 命令必须在LLM不可用时也能工作。

**修复方案（在 ChannelManager 的 `handleInbound` 中实现）：**
1. 收到消息后，先检查是否以 `/` 开头
2. 匹配已注册的命令（在 `registerCommands` 中存储命令定义）
3. 匹配成功 → 提取参数 → 直接走命令处理（`this.commandHandler?.(ctx)`）
4. 不进入 LLM 管道

```typescript
// 在 handleInbound 里加文本命令拦截
if (text.startsWith('/')) {
  const matched = this.registeredCommands.find(cmd => ...)
  if (matched) {
    const ctx: CommandContext = { ... }
    this.commandHandler?.(ctx)
    return // 不进 LLM
  }
}
```

**How to apply:** 以后新增通道 adapter，必须确认实现了 `onCommand`。同时 `handleInbound` 的文本命令拦截作为兜底保障，不管 adapter 有没有实现命令拦截，文本形式的 `/xxx` 命令都能被拦截。
