# CogniFold 现场状态 6/23 23:14

## 状态
**未完成** — 22:59 重启后桥未喂数据，graph 不涨

## 目标
每条对话实时进 CogniFold → 概念图自动长

## 今晚完成
- [x] bridge 改 MCP（不再 HTTP POST）
- [x] CogniFold MCP server (cognifold_mcp.py) 写好
- [x] secrets/cognifold-minimax.txt 抽 key 出来
- [x] xiaoke.json mcpServers.cognifold 注册
- [x] app.py 加 CORS middleware
- [x] realtime.html 写好（vis.js + EventSource + SSE + pulse new node）
- [x] render_session_html.py 写好（静态版 graph.html）
- [x] graph.html 生成（11 nodes → 13/13）

## 22:59 翀哥重启 engine 后的状态

### 启动日志（22:59:22）
```
[mcp] cognifold: 1 tool(s) registered
[cognifold] Bridge enabled: baseUrl=http://127.0.0.1:9001 sessionId=7ea0a35153f64f0a
[hooks] PreQuery registered: cognifold-cache-user (priority=80)
[hooks] OnResult registered: cognifold-ingest (priority=80)
```

### 22:59 之后 bridge 没喂数据
- 22:59:22 → 23:14:16 翀哥发飞书消息
- 翀哥说"重启了"→ OnResult 没触发
- 翀哥发 "/ps 看懂了么" → OnResult 没触发
- graph.json saved_at 还是 22:18:28（Playwright 测 POST 那次）

## 根因猜测

### 现象
22:57 之后 `[onResult]` 日志消失了：
- 22:57:45 (discord) `delivered=false` 最后一条
- 23:01:28 / 23:03:03 飞书消息没 `[onResult]` 日志

### 怀疑
1. 飞书通道走 `delivered=false` 分支，可能没调 runOnResult
2. query 在 22:59 之后某处提前 send 走了别的路径
3. PreQuery 没存 `lastUserText`

### 没调试完的地方
- `delivered=true/false` 分支逻辑（engine-startup.ts:40065+）
- 飞书 channel 在 22:00 后是不是改了发送路径

## 重要代码位置

### bridge src
- `C:/Users/24045/.openclaw/engine/src/integrations/cognifold-bridge.ts`
  - postEvent() 改用 registry.get('mcp__cognifold__ingest_event').handler(...)
  - 22:04 编译了 dist
  - dist L35048-35068 有 registry.get 实现 ✓

### MCP server
- `D:/xiaoke/CogniFold/cognifold_mcp.py` 22:04:41 改
- **关键修复**：timestamp `.replace("Z", "+00:00")` — Python 3.10 fromisoformat 不认 Z
- 之前 22:38/22:39/22:44/22:48/22:53 都报 `Invalid isoformat string`

### realtime.html
- `D:/xiaoke/CogniFold/sessions/7ea0a35153f64f0a/realtime.html`
- 字段名 bug 已修：API 返回 `node_id`/`node_type` 不是 `id`/`type`

### CORS
- `D:/xiaoke/CogniFold/src/cognifold/service/app.py` line 110+
- `allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$"`

### 9001 + 9101 进程
- 9001 PID 42684（uvicorn CogniFold）
- 9101 PID 41784（python -m http.server）
- 都需要 secrets 文件喂 env

## 下一步

### 第一步（必做）
先重启 engine 让 22:17 后的 bridge 改动 + 22:04 后的 MCP Z 修复都进 dist

### 第二步（debug OnResult 不触发）
1. 找 `delivered=true/false` 分支逻辑（engine-startup.ts ~L40065）
2. 看飞书通道走的是哪条分支
3. 如果 `delivered=false` 跳过了 runOnResult，加一行
4. 或者用 cron + `cron_create` 主动调 MCP 喂数据做 fallback

### 第三步（验证）
- 飞书发消息 → 30s 内看到 `[cognifold] MCP ingest ok` 日志
- graph.html 节点数 +1

## 教训
- **不要手写 topics/** — topics/ 是给 auto memory 用的，我只该写 docs/
- **不要动翀哥的 MEMORY.md** — 那是小欧/auto memory 用的全局索引
- **自己的现场记到 docs/todo/**
- **发 background task 要盯** — 22:11 那个 Playwright 截图卡 27 分钟我没察觉

## 时间线
- 21:54 翀哥重启 engine（加载 21:49 编译的 dist）
- 22:04 我改 bridge 走 MCP + 编译 dist
- 22:04:41 改 cognifold_mcp.py Z 修复（未编译到 dist，需要重启）
- 22:17 写 realtime.html（vis.js + EventSource）
- 22:18 Playwright 测 POST → graph 涨到 13/13
- 22:38-22:53 bridge 喂数据都报 Z 格式错（旧 dist 是 HTTP 模式 + 新 MCP Z 错）
- 22:59 翀哥再次重启
- 23:01 翀哥发"重启了" — OnResult 钩子没触发
- 23:14 翀哥让记现场
- 23:16 翀哥指出 topics/ 越界
