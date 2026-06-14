# Engine 显示模式设计文档

> 2026-06-12 小柯调研 + 起草，翀哥review后定稿

## 现状：Engine已经有display配置系统

**发现：** `config/display.ts` 已存在完整的DisplayConfig，`xiaoke.json` 171-208行已有`display`配置节点。

当前配置（小柯）：
```json
{
  "display": {
    "thinking":   { "enabled": true,  "emoji": "💭", "maxLen": 300 },
    "toolUse":    { "enabled": true,  "emoji": "🔧", "bashDisplayMode": "both" },
    "toolResult": { "enabled": false, "emoji": "📤", "showTools": ["TaskList","TaskGet","TaskCreate","TaskUpdate","TodoWrite","TeamCreate","edit"] },
    "reactions":  { "enabled": true,  "start": "👀", "done": "✅", "error": "❌" },
    "preview":    { "enabled": true,  "agentName": "小柯" },
    "typing":     { "enabled": true }
  }
}
```

**已经有的能力：**
- `toolUse.enabled` — 控制是否显示🔧tool call（true/false）
- `toolResult.enabled` — 控制是否显示📤tool result（true/false）
- `toolResult.showTools` — 即使enabled=false，这些工具的result强制显示
- `thinking.enabled` — 控制是否显示💭thinking
- `preview.enabled` — 控制流式preview
- `reactions.enabled` — 控制👀✅❌reaction

**缺失的：**
- 没有"模式"概念（work/daily一键切换）
- tool_progress没有三档（all/new/off），只有enabled=true/false
- 没有按平台分级覆盖的能力
- thinking控制只在显示层，没有控制是否让模型输出thinking

## 翀哥的反馈要点

1. **preview全保留** — "我觉得这个还挺好的"
2. **thinking（show_reasoning）要可配置** — 姐姐默认daily不需要，但她也可以自己打开
3. **tool_progress三档可配置** — 现在其实可配置（enabled true/false），但没有off档
4. **工作模式和日常模式** — 类似概念，需要一键切换
5. **姐姐搬过来默认daily** — 不让她突然"话多"

## 方案

### 方案1：在现有display节点上加mode字段（推荐）

不动display的细粒度配置，加一个`mode`字段做预设：

```json
{
  "display": {
    "mode": "daily",
    "thinking":   { "enabled": false },
    "toolUse":    { "enabled": false },
    "toolResult": { "enabled": false, "showTools": [] },
    "reactions":  { "enabled": true },
    "preview":    { "enabled": true },
    "typing":     { "enabled": true }
  }
}
```

**mode的预设覆盖：**

| mode | thinking | toolUse | toolResult | reactions | preview |
|------|----------|---------|------------|-----------|---------|
| `work` | 用户配置 | 用户配置 | 用户配置 | 用户配置 | 用户配置 |
| `daily` | false | false | false | true | true |

`work`模式 = 完全尊重display下各子项的配置
`daily`模式 = 强制thinking/toolUse/toolResult=false，其余尊重配置

**好处：**
- 改一个字段就能切换，不用改6个子配置
- 子配置仍然有效——切回work时恢复
- 向后兼容——不配mode就默认work（跟现在一样）

### 方案2：加platforms分级（后续可加）

参考Hermes的按平台覆盖，但当前两个平台（Discord/飞书）需求一样，暂不需要。

等姐姐搬过来如果需要不同平台不同显示再加。

### 改动范围

| 文件 | 改动 | 说明 |
|------|------|------|
| `config/display.ts` | 加mode字段+preset解析 | daily模式覆盖子项 |
| `config/loader.ts` | 透传mode | 无大改 |
| `engine-startup.ts` | onToolCall/onToolResult检查display | 已有enabled检查，确认生效 |
| `configs/xiaoke.json` | 加`"mode": "daily"` | 一行配置 |

**核心改动只有`config/display.ts`** — 加mode预设逻辑，大约20行代码。

### 姐姐配置（明天搬过来时）

```json
{
  "display": {
    "mode": "daily",
    "preview": { "enabled": true, "agentName": "小媒" },
    "reactions": { "enabled": true, "start": "👀", "done": "✅", "error": "❌" },
    "typing": { "enabled": true }
  }
}
```

日常聊天干干净净——只有preview流式输出 + 最终回复 + reactions。thinking/tool调用全部隐藏。
如果姐姐想看tool调用，自己改`mode: "work"`或`toolUse.enabled: true`。

### 切换方式

1. **配置文件** — 改xiaoke.json重启（最简单）
2. **Discord命令** — 后续可以加`/display work`/`/display daily`运行时切换（不急）

## Hermes参考

| 维度 | Hermes | Engine（本方案） |
|------|--------|-----------------|
| tool_progress三档 | all/new/off | mode=daily时off，mode=work时按配置 |
| show_reasoning | bool | thinking.enabled |
| preview | 跟全局 | 始终enabled（翀哥确认保留） |
| 平台分级 | 4级 | 暂不需要，后续可加 |
| cleanup | 可删tool气泡 | 不做，freeze保留 |

**跟Hermes的关键区别：** Hermes的tool_progress有`new`档（只显示新工具），Engine暂不加——`off`已经够用，`new`的逻辑（判断"新"vs"重复"）实现成本高收益低。
