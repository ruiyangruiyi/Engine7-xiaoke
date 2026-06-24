# PreQuery / OnResult 改造为 CC 兼容 hook 方案

> 日期：2026-06-24 | 作者：小柯 | 待 review：姐姐

## 背景

6/22 已建 `MessageHookRegistry`（`hooks/message-hooks.ts`），实现了 PreQuery 和 OnResult 两个 hook 点位的**进程内 callback 注册**。当前只有 engine 内部代码能注册（如 aim-sop-injection）。

翀哥要求：**以后用户安装时可以自己定义做什么 hook**，不改 engine 主流程。

调研 CC 原生 hook 系统后发现（详见 `docs/research/2026-06-24_CC原生hook调研.md`）：
- CC 用 `settings.json` 的 `hooks` 字段配置，支持 command/prompt/agent/http 四种 hook 类型
- hook 通过 **JSON stdin/stdout 协议** 与 engine 通信
- engine 已有完整的基础设施（`hooks/types.ts` + `hooks/executor.ts` + `hooks/config.ts`）

## 方案

### 核心思路

**把 PreQuery 和 OnResult 也走 CC 的 command hook 协议**——用户写 shell 脚本，engine 通过 stdin 传 JSON、解析 stdout 响应。

这样用户写 hook 的方式跟 CC 完全一致，不需要学两套。

### 新增两个 HookEvent

在 `hooks/types.ts` 的 `HOOK_EVENTS` 里加：

```typescript
'PreQuery',    // 消息进来后、LLM 前
'OnResult',    // LLM 回复后、发出去前
```

> ⚠️ CC 原生没有这两个事件——这是 engine 特有的（CC 没有消息渠道概念）。但协议格式完全对齐 CC。

### 用户配置格式

在 engine config 的 `hooks` 字段里写（对齐 CC settings.json）：

```json
{
  "hooks": {
    "PreQuery": [
      {
        "matcher": "feishu",
        "hooks": [
          {
            "type": "command",
            "command": "node ./hooks/spam-filter.js",
            "timeout": 5
          }
        ]
      }
    ],
    "OnResult": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ./hooks/add-signature.py",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

### Hook Input（JSON via stdin）

**PreQuery**：

```json
{
  "hook_event_name": "PreQuery",
  "session_id": "31f4532a-...",
  "channel": "feishu",
  "channel_id": "oc_xxx",
  "channel_type": "dm",
  "from": "ou_xxx",
  "from_name": "翀哥",
  "text": "用户发来的消息",
  "is_mentioned": false,
  "is_bot": false
}
```

**OnResult**：

```json
{
  "hook_event_name": "OnResult",
  "session_id": "31f4532a-...",
  "channel": "feishu",
  "channel_id": "oc_xxx",
  "channel_type": "dm",
  "from": "ou_xxx",
  "from_name": "翀哥",
  "response": "LLM 生成的回复",
  "input_tokens": 5000,
  "output_tokens": 800
}
```

### Hook Output（JSON via stdout 或 exit code）

**对齐 CC syncHookResponseSchema**：

```json
{
  "continue": false,
  "stopReason": "被垃圾过滤拦截"
}
```
→ 不进 LLM / 不发回复

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreQuery",
    "additionalContext": "注入到对话的额外上下文"
  }
}
```
→ 改消息内容 / 注入上下文

**exit code 2** = blocking（对齐 CC 协议），stderr 内容作为 blocking 原因。

**纯文本 stdout** = 不拦截，仅记日志。

### matcher 语义

| 事件 | matcher 匹配什么 | 示例 |
|------|-----------------|------|
| PreQuery | channel 名称（`feishu` / `discord` / `wechat` / `oac`） | `"matcher": "feishu"` 只拦截飞书消息 |
| OnResult | channel 名称 | `"matcher": "discord"` 只处理 Discord 回复 |

`matcher` 为空或不写 = 匹配所有渠道。

### 执行流程

```
消息进来
  ↓
① MessageHookRegistry.runPreQuery()  ← 进程内 callback（现有逻辑，aim-sop 等）
  ↓
② executeHooks('PreQuery', ...)      ← 新增：走 CC command hook 协议（用户脚本）
  ↓
dispatcher.submitMessage()           ← 入队
  ↓
LLM 推理
  ↓
③ MessageHookRegistry.runOnResult()  ← 进程内 callback（现有逻辑，敏感词等）
  ↓
④ executeHooks('OnResult', ...)      ← 新增：走 CC command hook 协议（用户脚本）
  ↓
channelManager.send()                ← 发出去
```

**①② 和 ③④ 各自串行**，任何一个返回 skip 就终止链。

## 与现有 MessageHookRegistry 的关系

**不替换，叠加**：

- `MessageHookRegistry`（进程内 callback）= engine 内部逻辑用（aim-sop、blocklist、敏感词）
- `executeHooks`（CC command hook）= 用户自定义脚本用

两者串行执行：先跑进程内 callback，再跑用户 command hook。

## 文件改动

| 文件 | 操作 | 内容 |
|------|------|------|
| `hooks/types.ts` | 改 | HOOK_EVENTS 加 `PreQuery` `OnResult`；加对应的 HookInput 类型 |
| `hooks/executor.ts` | 改 | 加 `executePreQueryHooks()` 和 `executeOnResultHooks()` 便捷方法 |
| `engine-startup.ts` | 改 | PreQuery 链后加 `executeHooks('PreQuery')`；OnResult 链后加 `executeHooks('OnResult')` |
| `hooks/index.ts` | 改 | 导出新方法 |

**不需要改的**：
- `hooks/message-hooks.ts` — 不动，跟 command hook 并行
- `hooks/config.ts` — 已经支持从 config 读 hooks，天然兼容

## 用户 Hook 脚本示例

```javascript
// hooks/spam-filter.js
let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  const { text, from_name } = JSON.parse(input);
  
  // 简单垃圾过滤
  if (text.includes('加微信免费领')) {
    console.log(JSON.stringify({
      continue: false,
      stopReason: `垃圾消息已拦截（来自 ${from_name}）`
    }));
    process.exit(0);
  }
  
  // 放行
  process.exit(0);
});
```

## 风险

1. **command hook 是 spawn 子进程**——有性能开销（~50-200ms），PreQuery 链串行执行可能增加消息延迟。建议用户 hook 控制在 1-3s 内。
2. **PreQuery 的 skip 语义**——用户脚本返回 `continue: false` 会阻止消息进 LLM，需在文档里强调。
3. **进程内 callback 和 command hook 的执行顺序**——固定 callback 先、command 后，不支持混排 priority。

## 待姐姐 review 的决策点

1. **PreQuery / OnResult 是否加进 HOOK_EVENTS**——加进去就跟 CC 的 27 个事件并列，但这两个是 engine 独有的
2. **用户 hook 配置写在哪**——engine config 的 hooks 字段？还是单独一个 `hooks.json`？
3. **进程内 callback 和 command hook 的顺序**——callback 先 command 后？还是可以混排？
4. **matcher 匹配 channel 还是 from**——我倾向 channel（更通用），但可能有按用户过滤的需求

## 验证标准

1. 写一个 `echo.js` 脚本，配到 config hooks PreQuery 里，飞书发消息能看到 stdin JSON
2. hook 返回 `continue: false`，消息不进 LLM
3. hook 返回纯文本 stdout，消息正常进 LLM（不拦截）
4. 进程内 callback（aim-sop）和 command hook 都正常执行，互不干扰
