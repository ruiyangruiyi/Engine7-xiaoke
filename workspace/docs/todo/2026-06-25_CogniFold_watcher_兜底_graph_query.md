# CogniFold watcher 兜底 + graph query 接入

## 背景

- 6/24 已完成 CogniFold 流式接入（bridge.ts + engine-startup.ts + intent-watcher.ts）
- watcher 收到 SSE `proactive_suggestion` event → 写 .cognifold-proactive.json → dispatcher.submitMessage 注入 main session
- 链路在"IntentSelector → ActionQueue"是断的：intent 进 graph 后 action 不会自动生成（要等 CogniFold Python 改）
- 娘说"先跑起来再说"，CogniFold Python 侧爹拍板先不动

## 目标

engine 侧 watcher 加**数据完整性兜底**：
1. SSE 收到 proactive_suggestion 但 suggestion 字段不全（缺 description/title/related_concepts）→ 用 intent_id 调 graph query 补全
2. 补全后写 .cognifold-proactive.json
3. 然后再走 dispatcher.submitMessage 注入

不改 CogniFold Python 侧，只在 engine 侧做兜底。

## 改动文件

- `engine/src/engine-startup.ts` — watcher 回调里加 graph query 兜底逻辑

## 任务拆解

### Task 1: 改 engine-startup.ts 兜底逻辑

**位置：** `engine/src/engine-startup.ts` L2381-2392 (suggestions 写入前)

**逻辑：**
- 收到 proactive_suggestion 时，对每条 suggestion 检查 description 是否完整
- 不完整时，用 `intent_id` 调 `GET /api/v1/sessions/{sessionId}/graph/nodes/{nodeId}` 兜底
- 用 graph 节点的 data 字段补全
- 补全失败 warn log 继续走原流程

**接口路径**（实测验证）：
```
GET http://127.0.0.1:9001/api/v1/sessions/86028fda52774069/graph/nodes/{node_id}
→ {node_id, node_type, data: {title, description, ...}, ...}
```

sessionId = `86028fda52774069`（不是 xiaoke-graph 默认值）

**伪代码：**
```typescript
async function enrichSuggestion(s: any): Promise<any> {
  if (s.intent_id && (!s.description || !s.title)) {
    try {
      const url = `${baseUrl}/api/v1/sessions/${sessionId}/graph/nodes/${s.intent_id}`
      const resp = await fetch(url, { headers: { Accept: 'application/json' } })
      if (resp.ok) {
        const node = await resp.json()
        if (node.data) {
          return { ...s, title: s.title || node.data.title, description: s.description || node.data.description, status: s.status || node.data.status }
        }
      }
    } catch (e: any) {
      console.warn(`[cognifold] graph node 兜底失败: ${e.message}`)
    }
  }
  return s
}

const enriched = await Promise.all(timestamped.map(enrichSuggestion))
```

**验证：**
- 编译通过
- 完整 data 时不打额外日志
- 不完整 data 时调 `/graph/nodes/{id}` 补全
- 兜底失败时 warn 不阻塞

### Task 2: 写测试场景文档

记录：
- 完整 data 场景：直接走原流程，不调 query
- 不完整 data 场景：调 query 兜底补全
- query 失败场景：warn log 继续走原流程（不阻塞）

## 风险

- graph query 接口路径要确认是 `/api/v1/sessions/{sessionId}/query` 而不是别的（娘给的）
- sessionId 是 `86028fda52774069` 不是 `xiaoke-graph`（默认值）
- 接口可能在 SSE 推送前已经晚了——但只是兜底，迟到总比缺好

## 验证标准

- TS 编译通过
- watcher 回调拿到完整 data 时不打额外日志
- watcher 回调拿到不完整 data 时能调 query 补全
- query 失败时 warn log 不阻塞流程
