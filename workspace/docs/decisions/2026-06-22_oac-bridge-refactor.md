# OAC Bridge 模块重构 Implementation Plan

> **For agentic workers:** inline execution.

**Goal:** 把 engine-startup.ts 里的 OAC webhook 业务逻辑抽出到 `src/integrations/oac-bridge.ts`，只留一行注册调用。

**Architecture:** 新建 `src/integrations/` 目录放第三方集成模块。`oac-bridge.ts` 导出一个 `registerOacBridge()` 函数，收 httpServer/messageHooks/dispatcher/deps/config 参数，在函数内完成 webhook endpoint + OnResult hook 注册。

**Tech Stack:** TS, Node.js http module, fetch

## Global Constraints

- 不准改 OAC 源码
- 不准改 hook 架构主体（`message-hooks.ts`）
- 不准改其他已有代码（OAC block 之外的东西一根手指不动）
- rebuild 通过后才能说完成

---

### Task 1: 读引擎代码，确认要抽的两个块精确位置

**Files:** `C:/Users/24045/.openclaw/engine/src/engine-startup.ts`

- [ ] **Step 1: 读 OnResult hook 块（~L517-535）**

- [ ] **Step 2: 读 webhook endpoint 块（~L2326-2370）**

- [ ] **Step 3: 确认 import 和依赖传递关系**
  - `messageHooks` 从 `'./hooks/message-hooks.js'` 引入（`registerOnResult`）
  - `dispatcher` 当前作用域变量
  - `deps` 当前作用域变量（HandleQueryDeps）
  - `config` 当前作用域变量
  - `CONTEXT_API_PORT` 在 httpServer 上面计算的

---

### Task 2: 创建 src/integrations/oac-bridge.ts

**Files:**
- Create: `C:/Users/24045/.openclaw/engine/src/integrations/oac-bridge.ts`

- [ ] **Step 1: 确认 `src/integrations/` 目录存在**

Run: `ls C:/Users/24045/.openclaw/engine/src/integrations/`
Expected: 目录存在或创建

- [ ] **Step 2: 写 oac-bridge.ts**

```typescript
// OAC Bridge — OpenAvatarChat 集成模块
// 独立的 webhook endpoint + OnResult hook，不污染 engine-startup.ts

import type { MessageDispatcher } from '../core/message-dispatcher.js'
import type { HandleQueryDeps } from '../handle-query.js'
import type http from 'node:http'
import { messageHooks } from '../hooks/message-hooks.js'

export function registerOacBridge(
  httpServer: http.Server,
  dispatcher: MessageDispatcher,
  deps: HandleQueryDeps,
  config: any,
): void {
  const portSuffix = (config.api?.port || 16890) !== 16890 ? `:${config.api?.port || 16890}` : ''

  // === OnResult hook — 回复 POST 回 OAC ===
  messageHooks.registerOnResult('oac-bridge-reply', async (ctx) => {
    if (ctx.inbound.channel !== 'oac') return null
    const oacCallbackUrl = (config as any)?.oacBridge?.callbackUrl || 'http://localhost:8011/oc-reply'
    const oacSessionId = ctx.inbound.from
    try {
      const resp = await fetch(oacCallbackUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ oac_session_id: oacSessionId, text: ctx.response }),
      })
      console.log(`[oac-bridge] Reply POST ${oacCallbackUrl}: ${resp.status} (${ctx.response.length} chars)`)
    } catch (err: any) {
      console.error(`[oac-bridge] Reply POST failed: ${err.message}`)
    }
    return { skip: true }
  }, 30)

  // === Webhook endpoint insertion ===
  // engine-startup.ts 的 httpServer 路由里注入 /webhook/oac-bridge
  // 我们通过 monkey-patch 原始 httpServer 的 listener，注入到现有路由
  // 但更干净的做法：在 engine-startup.ts 里加一行 registerOacBridge(httpServer, ...)
  // 这里只导出函数，不注册——由 engine-startup.ts 在适当位置调用
}

// 注：webhook endpoint 也抽到这里，但 engine-startup.ts 的 httpServer
// 路由判断在已有的 if/else 链里。最简单的方式：在函数内部重新 addListener？
// 不对——httpServer 的 request listener 只能有一个。
// 
// 方案：把 webhook 判断逻辑作为函数导出，engine-startup.ts 在路由链里调用
// 但娘说"engine-startup.ts 里只留一行 registerOacBridge(...)"
// 
// 所以 webhook endpoint 也需要在 registerOacBridge 内部完成。
// 方案：用 server.prependListener('request', handler) 加在高优先级
// 或把原本的 request listener 存起来再 wrap

export function createOacWebhookHandler(
  dispatcher: MessageDispatcher,
  deps: HandleQueryDeps,
): (req: http.IncomingMessage, res: http.ServerResponse) => boolean {
  return async (req, res) => {
    if (req.method !== 'POST' || req.url !== '/webhook/oac-bridge') return false

    try {
      let body = ''
      for await (const chunk of req) body += chunk
      const { oac_session_id, text, sender_name } = JSON.parse(body)
      if (!oac_session_id || !text) {
        res.writeHead(400, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ error: 'Missing oac_session_id or text' }))
        return true
      }
      console.log(`[oac-bridge] Received from ${oac_session_id}: ${text.slice(0, 80)}`)

      const oacSessionId = 'oac:' + oac_session_id
      dispatcher.submitMessage({
        text,
        sessionId: oacSessionId,
        channelName: 'oac',
        channelTarget: oac_session_id,
        inboundMeta: {
          content: text,
          from: oac_session_id,
          fromName: sender_name || 'OAC User',
          channel_id: oac_session_id,
          channel: 'oac',
          channelType: 'dm',
        },
        source: 'user',
        priority: 'next',
        deps,
      })
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: true }))
    } catch (err: any) {
      console.error(`[oac-bridge] Error: ${err.message}`)
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: err.message }))
    }
    return true
  }
}
```

- [ ] **Step 3: 把 oac-bridge.ts 分成：导出 `registerOacBridge()` 一个函数，内部完成全部注册**
  上面写的有两个导出函数，不好。应该一个函数搞定：在 registerOacBridge 内部 wrap 原始 httpServer 的 request listener。

---

### Task 3: 重构 engine-startup.ts — 替换两处为单行调用

**Files:** `C:/Users/24045/.openclaw/engine/src/engine-startup.ts`

- [ ] **Step 1: 添加 import**

在 import 区域加：
```typescript
import { registerOacBridge } from './integrations/oac-bridge.js'
```

- [ ] **Step 2: 删除 OnResult hook 块（当前 L517-535）**

删除 `messageHooks.registerOnResult('oac-bridge-reply', ...)` 块

- [ ] **Step 3: 删除 webhook endpoint 块（当前 L2326-2370）**

删除 `// === OAC Bridge webhook ===` 到 `if (req.method === 'POST' && req.url === '/webhook/oac-bridge') { ... }` 块

- [ ] **Step 4: 在 httpServer.listen 前加一行调用**

```typescript
registerOacBridge(httpServer, dispatcher, deps, config)
```

---

### Task 4: Rebuild 验证

- [ ] **Step 1: rebuild**
```bash
cd C:/Users/24045/.openclaw/engine && npx eslint . --ext .ts 2>&1 | tail -5
```
不对——engine 没配 eslint。直接用 esbuild rebuild:
```bash
cd C:/Users/24045/.openclaw/engine && npx esbuild src/main.ts --bundle --platform=node --format=esm --outdir=dist --out-extension:.js=.mjs --sourcemap --external:discord.js --external:@discordjs/voice --external:@discordjs/ws --external:turndown --external:sharp --external:@modelcontextprotocol/sdk --external:axios --external:@larksuiteoapi/node-sdk --external:form-data --external:combined-stream --allow-overwrite 2>&1
```
Expected: `⚡ Done in < 2s`

- [ ] **Step 2: 清理 stop-test.log（测试遗留）**
```bash
rm D:/xiaoke/tmp/stop-test.log 2>/dev/null; rm D:/xiaoke/tmp/stop-test.lock 2>/dev/null; echo done
```

---

## 收尾条件
1. rebuild 通过
2. 功能不变（娘 curl 验证过的逻辑原样迁移）
3. engine-startup.ts 只有一行 OAC 相关代码
