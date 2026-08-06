# OAC Webhook 消息进出链路设计

> 日期：2026-06-22 | 作者：小柯 | 决策者：翀哥 | 方案 B

## 决策

翀哥拍板方案 B：webhook 进 engine + POST 出回 OAC callback。**不混 channelManager，走独立逻辑。**

## 现有基础设施

### Engine 已有 HTTP server（复用不新开端口）
- **端口**：16890（basePort，config.api.port）+ profile hash offset
- **路由**：`/api/context`（context usage）
- **代码位置**：`engine-startup.ts:2235-2283`
- **扩展点**：在同一个 `createServer` 回调里加 `/webhook/oac-bridge` 路由

### Dispatcher 是统一消息入口
- `dispatcher.submitMessage({ text, sessionId, channelName, channelTarget, source, deps })`
- 所有输入（Discord/飞书/微信/cron/heartbeat）都走这
- OAC 进来的消息也走这——`channelName='oac'`

### 出站走 onResult 回调
- `engine-startup.ts:1942`：`channelManager.send(inbound.channel, ...)`
- **OAC 消息不走这**——判断 `inbound.channel === 'oac'` 时 POST 回 OAC callback

## 数据流

### 进来（OAC → Engine）

```
OAC ChatAgent
    │
    │ POST http://localhost:16890/webhook/oac-bridge
    │ Body: { oac_session_id, text, sender_name }
    │
    ▼
Engine httpServer (engine-startup.ts:2235)
    │ 新增路由: /webhook/oac-bridge
    │ 解析 body → 转成 InboundMessage
    │
    ▼
dispatcher.submitMessage({
  text: body.text,
  sessionId: 'oac:' + body.oac_session_id,  // 独立 session 空间
  channelName: 'oac',
  channelTarget: body.oac_session_id,       // 回复时用
  source: 'user',
  deps: msgDeps,
})
    │
    ▼
正常 LLM 流程 (system prompt + memory + tools)
```

### 出去（Engine → OAC）

```
LLM 回复完成
    │
    ▼
onResult 回调 (engine-startup.ts:~1942)
    │
    │ 判断 inbound.channel === 'oac'
    │ → 跳过 channelManager.send
    │ → 走 OAC 回复路径
    │
    ▼
POST http://localhost:8011/oc-reply
Body: { oac_session_id, text }
    │
    ▼
OAC OcChannelClient callback
    │ 收到 text
    ▼
TTS (CosyVoice) → Avatar (MuseTalk) → WebRTC 推流
```

## 需要改的代码

### 改动 1：httpServer 加路由（~30 行）

`engine-startup.ts:2235` 的 `http.createServer` 回调里加：

```typescript
// 新增: OAC Bridge webhook
if (req.url === '/webhook/oac-bridge' && req.method === 'POST') {
  let body = ''
  req.on('data', chunk => body += chunk)
  req.on('end', () => {
    try {
      const { oac_session_id, text, sender_name } = JSON.parse(body)
      if (!oac_session_id || !text) {
        res.writeHead(400, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ error: 'missing oac_session_id or text' }))
        return
      }

      // 构造 inbound（不走 channelManager.handleInbound，直接进 dispatcher）
      const sessionId = sessions.getSessionId('oac:' + oac_session_id) || 'oac:' + oac_session_id
      dispatcher.submitMessage({
        text,
        sessionId,
        channelName: 'oac',
        channelTarget: oac_session_id,
        source: 'user',
        deps: msgDeps,
        inboundMeta: {
          from: oac_session_id,
          fromName: sender_name || 'OAC User',
          channel: 'oac',
          channel_id: oac_session_id,
          channelType: 'dm',
        },
      })

      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: true, sessionId }))
    } catch (err: any) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: err.message }))
    }
  })
  return
}
```

### 改动 2：onResult 加 OAC 回复分支（~15 行）

`engine-startup.ts:~1942` 的 `channelManager.send` 前面加判断：

```typescript
// OAC 消息不走 channelManager，直接 POST 回 OAC callback
if (inbound.channel === 'oac') {
  const oacSessionId = inbound.channel_id
  const oacCallbackUrl = `http://localhost:8011/oc-reply`
  try {
    await fetch(oacCallbackUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ oac_session_id: oacSessionId, text: finalResponse }),
    })
    console.log(`[oac-bridge] Reply sent to ${oacSessionId} (${finalResponse.length} chars)`)
  } catch (err: any) {
    console.error(`[oac-bridge] Reply failed: ${err.message}`)
  }
} else {
  // 正常 Discord/飞书/微信回复
  channelManager.send(inbound.channel, inbound.channel_id, finalResponse, opts).catch(...)
}
```

### 改动 3：config 加 OAC 配置（可选）

`engine-config.json` 加：

```json
{
  "oac": {
    "enabled": true,
    "callbackUrl": "http://localhost:8011/oc-reply",
    "sessionPrefix": "oac:"
  }
}
```

## Session 管理

OAC 每个连接一个 `oac_session_id`（OAC 自己生成）。Engine 用 `oac:{oac_session_id}` 作为 sessionId。

- 同一个 OAC 用户多次对话 → 同一个 oac_session_id → 同一个 engine session → 有上下文记忆
- OAC 断开重连 → 新 oac_session_id → 新 session（符合"电话"语义）

## 不走 channelManager 的原因

1. **OAC 不是文本 channel**——没有 typing indicator、没有 preview、没有 reaction
2. **OAC 回复路径不同**——POST HTTP 而不是调平台 API
3. **OAC 消息格式不同**——带 oac_session_id，不带 platform messageId
4. **保持 channelManager 干净**——OAC 是独立"电话"业务，不混通用 channel 逻辑

## 配置体系

### Engine 配置（configs/xiaoke.json）
```json
{
  "api": { "port": 16890 },
  "oac": {
    "enabled": true,
    "callbackUrl": "http://localhost:8011/oc-reply"
  }
}
```

### OAC 配置（config/chat_with_..._agent.yaml）
```yaml
handler_configs:
  oc_bridge:
    module: handlers.agent.oc_bridge
    gateway_url: http://localhost:16890
    webhook_path: /webhook/oac-bridge
    callback_port: 8011
    callback_path: /oc-reply
```

## 延迟预算

| 环节 | 延迟 |
|------|------|
| VAD 端点检测 | ~500ms-2s（改 end_delay） |
| ASR paraformer | ~65ms |
| Webhook HTTP（localhost） | ~2ms |
| Engine LLM 首 token | 300-800ms |
| POST 回 OAC（localhost） | ~2ms |
| TTS CosyVoice 首句 | 200-500ms |
| Avatar MuseTalk | 30-50ms/帧 |
| **全链路首字** | **~1-3s** |

## 验证步骤

1. **curl 测 webhook**：`curl -X POST http://localhost:16890/webhook/oac-bridge -d '{"oac_session_id":"test","text":"你好","sender_name":"test"}'`
2. **看 engine log**：是否收到消息、走 dispatcher、LLM 回复
3. **OAC 启动**：配 oc_bridge handler，看是否连上 engine
4. **端到端**：浏览器开 OAC → 说话 → 听到回复

## 后续优化（不在这次）

- **流式回复**：LLM stream token → 分段 POST 给 OAC（不等完整回复）
- **打断**：用户说话时 stop 当前 OAC session 的 query
- **视觉注入**：OAC Perception 的描述作为 system dynamic 注入 LLM
