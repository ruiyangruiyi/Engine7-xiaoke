# API 请求结构：tools / messages / system prompt 的位置

> 调研时间：2026-06-30
> 源码：`engine/src/models/anthropic-provider.ts` + `engine/src/models/openai-provider.ts`

## 一图看懂

发给大模型的请求就是一个 HTTP POST，body 是 JSON。三个核心部分**平级**：

```
POST /v1/messages (Anthropic)  或  /chat/completions (OpenAI)
{
  "model": "glm-5.2",
  "messages": [ ... ],       ← 聊天记录
  "system": "...",            ← 系统提示词（位置因格式不同）
  "tools": [ ... ]            ← 工具列表（含完整 schema）
}
```

**tools 不在 messages 里，不在 system 里，是请求体的顶层独立字段。**

---

## Anthropic 格式（GLM/智谱 用这个）

```json
{
  "model": "glm-5.2",
  "messages": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "..." }
  ],
  "system": [
    { "type": "text", "text": "固定 prompt（stable）", "cache_control": {"type":"ephemeral"} },
    { "type": "text", "text": "每轮动态 prompt（dynamic）" }
  ],
  "tools": [
    {
      "name": "read",
      "description": "读取文件",
      "input_schema": { "type": "object", "properties": { ... } }
    }
  ],
  "thinking": { "type": "enabled", "budget_tokens": 8192 }
}
```

### 关键点

| 部分 | 位置 | 格式 |
|------|------|------|
| system prompt | 顶层 `system` 字段，是 content blocks 数组 | stable 带缓存 + dynamic 无缓存 |
| tools | 顶层 `tools` 字段 | 每个工具：name + description + input_schema |
| messages | 顶层 `messages` 字段 | role + content |

### system prompt 的两段

```
systemStable  → { type: "text", text: "...", cache_control: {type:"ephemeral"} }
systemDynamic → { type: "text", text: "..." }
```

stable 部分带 `cache_control`，API 端做 prompt cache。dynamic 每轮变化（时间戳、工具状态等），不缓存。

**之前 ToolSearch 开启时**，deferred 工具列表注入在 systemDynamic 里：
```
<available-deferred-tools>
TodoWrite
EnterPlanMode
...
</available-deferred-tools>
These tools are available but their schemas are not loaded yet...
```

现在 toolSearch.enabled=false，这段不再生成。

---

## OpenAI 格式

```json
{
  "model": "gpt-4o",
  "messages": [
    { "role": "system", "content": "固定 prompt\n\n每轮动态 prompt" },
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "..." }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "read",
        "description": "读取文件",
        "parameters": { "type": "object", "properties": { ... } }
      }
    }
  ]
}
```

### 关键区别

| 维度 | Anthropic | OpenAI |
|------|-----------|--------|
| system prompt | 顶层 `system` 字段 | 塞进 `messages[0]`（role: system） |
| stable + dynamic | 分两个 content block，stable 带缓存 | 合并成一个字符串 |
| tools 字段名 | `tools` | `tools` |
| tools schema 格式 | `input_schema` | `parameters`（嵌套在 `function` 里） |
| tools 工具格式 | `{ name, description, input_schema }` | `{ type:"function", function: {name, description, parameters} }` |
| thinking | 支持（`thinking` 字段） | 不支持 |
| prompt cache | 显式 `cache_control` | API 自动 prefix 匹配 |

---

## Engine 的实际代码位置

### Anthropic Provider (`anthropic-provider.ts`)

```
L178: url = baseUrl + "/v1/messages"
L179-203: 构建 body
  L181: messages = formatted（聊天记录）
  L195: system = systemBlocks（stable + dynamic）
  L196-202: tools = 每个工具转 {name, description, input_schema}
  L185-193: thinking 配置
```

### OpenAI Provider (`openai-provider.ts`)

```
L68: url = baseUrl + "/chat/completions"
L70-77: 构建 body
  L72: messages = formatted（system 在 messages[0]）
  L74: tools = 直接透传 ToolDefinition[]
  L61: system = stable + dynamic 合并为一个字符串，塞进 messages[0]
```

---

## 为什么 .context-debug.txt 看不到 tools

`.context-debug.txt` 只遍历打印 `messages` 数组（handle-query.ts L528-568）。

tools 是独立的顶层字段，不在 messages 里，所以不会出现在 debug 文件中。

要看 tools 内容，查 engine log 里 `[anthropic] →` 开头的行：
```
[anthropic] → model=glm-5.2 ... tools=62: read, write, edit, glob, ...
```
这行打印了工具数量和名字列表。
