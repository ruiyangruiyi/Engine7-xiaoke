# CogniFold 验证步骤 6/24

## 状态
- ✅ bridge MCP 端到端跑通（08:50 翀哥"继续吧 小柯"触发，graph 13→31）
- ✅ intent-watcher.ts 写好 + SSE 连接验证（dist/integrations/cognifold-intent-watcher.mjs）
- ⏳ xiaomei.json 接入 — 等翀哥配
- ⏳ 多轮真实对话验证 — 等翀哥重启引擎

## 翀哥要的真实场景验证流程

### 1. 翀哥重启引擎
- 走 start.cmd（不发明新命令）
- 加载最新 dist（含 bridge MCP + intent-watcher + Z 修复）

### 2. 翀哥在飞书真实聊几轮
- 不要 curl / 不要 test 脚本
- 真的发飞书消息说几句话
- 建议测的话：
  - "今天下午有空吗"（日常）
  - "CogniFold 那个 graph 涨了没"（问进度）
  - "给我看下 graph.html"（看可视化）
  - "我等下去开会"（报行程）
- 每条都要让 LLM 抽概念/意图

### 3. 验证每轮 graph 都涨
- 看 `/d/xiaoke/logs/engine-2026-06-24.log`
- grep `[cognifold] MCP ingest ok` 应该每条对话都有
- 每次 ops_completed > 1 = 抽到东西
- 偶尔 ops=1（只 add event）也正常

### 4. 验证 intent_emerged 触发
- 飞书聊 3-5 轮后，至少应该有 1 个 intent 被抽出
- 看 realtime.html 的 log：搜 `intent_emerged` 关键字
- 或者 grep engine 日志看 SSE publish 行

### 5. 看 graph.html
- 路径：`/Users/chongzhang/xiaoke//CogniFold/sessions/7ea0a35153f64f0a/graph.html`
- 节点应该有颜色（event 蓝 / concept 绿 / intent 橙）
- 边应该连接（source_id → target_id，labels 显示 edge_type）
- 当前 31 nodes / 62 edges，验证后应 > 50 nodes

## 验证完成标准（block 之前必须 ✅）
- [ ] 5 轮真实飞书对话
- [ ] 每轮都看 `[cognifold] MCP ingest ok`
- [ ] graph 涨到 > 50 nodes
- [ ] 至少看到 1 次 `intent_emerged`
- [ ] graph.html 渲染正常有颜色有边

## 现在等翀哥回来

翀哥说"得验证完再收工"——我没 block。继续看 SOP 流程、准备验证工具，不主动推进大改。
