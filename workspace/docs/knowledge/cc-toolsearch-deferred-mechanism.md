# CC ToolSearch / Deferred Tools 机制调研

> 调研时间：2026-06-30
> 源码位置：`D:/work/start-claude-code/`（CC v2.1.185 可读源码）

## 1. CC 的 ToolSearch 开关机制

**核心文件**：`src/utils/toolSearch.ts`

### 三种模式

| 模式 | 含义 | 触发条件 |
|------|------|----------|
| `standard` | 关闭，全部工具 inline | `ENABLE_TOOL_SEARCH=0` 或 `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` |
| `tst` | 强制开启，deferred 工具按需加载 | `ENABLE_TOOL_SEARCH=1`（也是**默认值**） |
| `tst-auto` | 自动，按工具数量阈值 | `ENABLE_TOOL_SEARCH=auto` 或 `auto:N` |

### 判定逻辑（`isToolSearchEnabled`）

```
1. 模型不支持 tool_reference → 关闭（haiku 等）
2. ToolSearchTool 被 disallow → 关闭
3. 模式判断：
   - standard → 关闭
   - tst → 开启
   - tst-auto → 检查工具数量阈值
4. 没有 deferred 工具 → 关闭（没意义）
```

### 关键发现

- **CC 默认开启** (`return 'tst'`)，但仅对支持 `tool_reference` 的模型
- **不支持 tool_reference 的模型自动关闭**——GLM 属于这类
- CC 用 API 端 `defer_loading: true` 让 Claude 原生处理，不传 schema 只传名字
- `auto:N` 模式：按概率随机决定，N=0 全开，N=100 全关

## 2. CC 的工具排序

**核心文件**：`src/services/api/claude.ts` L1160

### 结论：CC 不排序

```typescript
// L1160-1167
filteredTools = tools.filter(tool => {
  if (!deferredToolNames.has(tool.name)) return true  // 非 deferred 全留
  if (toolMatchesName(tool, TOOL_SEARCH_TOOL_NAME)) return true  // ToolSearch 留
  return discoveredToolNames.has(tool.name)  // 已发现的 deferred 留
})
```

- tools 数组保持**注册顺序**，无额外排序
- ToolSearch 最后注册所以排最后（自然顺序）
- CC 不需要排序是因为 **Claude 对工具顺序不敏感**

### Engine 的差异

| 维度 | CC | Engine |
|------|-----|--------|
| API 支持 | `defer_loading: true` 原生支持 | GLM 不支持，Engine 自己管 |
| 排序 | 不排（注册顺序） | 需要排（GLM 对顺序敏感） |
| ToolSearch 默认 | 开启（Claude 支持） | **关闭**（GLM 不支持 tool_reference） |

## 3. CC 的 deferred 判定

**核心文件**：`src/tools.ts` 的 `isDeferredTool`

CC 的判定逻辑：
- `tool.alwaysLoad === true` → 不 defer
- `tool.isMcp === true` → defer（MCP 工具统一 defer）
- `tool.shouldDefer === true` → defer
- `name === TOOL_SEARCH_TOOL_NAME` → 不 defer

## 4. 对 Engine 的影响

### 为什么 GLM 上 ToolSearch 是灾难

1. GLM 不支持 `defer_loading`——Engine 必须自己管 tools 数组
2. GLM 对工具顺序敏感——看到 ToolSearch 排前面就倾向于先搜
3. 名字 "ToolSearch" 本身诱导搜索行为——即使改了 description 也无效
4. Engine 加了白名单排序 + ToolSearch 垫底，但 GLM 还是忍不住搜

### Engine 的解决方案

- **config.toolSearch.enabled = false**（默认关闭）
- 关闭时：全部工具走 active，ToolSearch 从 tools 数组剔除
- 开启时：走白名单 + 排序机制（给未来换 Claude 留着）
- 改名 `ToolSearch` → `load_missing_tools`（降低诱导）

## 5. 子 Agent 的工具列表

CC 子 agent 工具不共享父 agent 列表：

| Agent Type | 工具配置 |
|------------|----------|
| general-purpose | `tools: ['*']`（全量继承） |
| Explore | 白名单：read, grep, glob, exec, web_search, web_fetch |
| Plan | 黑名单：disallowedTools |

子 agent 不走 deferred 机制，直接按 type 配置给 schema。

## 文件索引

| 文件 | 作用 |
|------|------|
| `src/utils/toolSearch.ts` | 开关判定、模式选择 |
| `src/services/api/claude.ts` L1120-1170 | tools 数组组装 |
| `src/constants/tools.ts` | 工具常量定义 |
| `src/tools/ToolSearchTool/prompt.ts` | ToolSearch 描述 |
