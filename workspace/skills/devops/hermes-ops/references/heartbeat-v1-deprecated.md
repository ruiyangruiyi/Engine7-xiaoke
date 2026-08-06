# 旧心跳Relay方案（已废弃，2026-05-02）

## 架构（webhook relay）

Cron → `heartbeat_relay.py` → POST到webhook endpoint → 独立webhook session → deliver飞书

每次心跳都创建全新独立session（`webhook:heartbeat-relay:<delivery_id>`），不复用已有session。

## 废弃原因

1. **无连续记忆**：cron不在主session执行，relay到webhook也创建隔离session
2. **空转烧token**：glm-5.1每次都跑LLM但90%以上时候输出[SILENT]，触发API限速
3. **双链路重复**：cron prompt→deliver 和 relay→webhook→deliver 可能同时触发
4. **进程崩溃无检测**：4/27 Hermes进程挂了，心跳没有自愈能力，小柯失联5天

## 旧方案源码证据

- webhook session_id: `gateway/platforms/webhook.py` L424 `session_chat_id = f"webhook:{route_name}:{delivery_id}"`
- cron隔离session: `cron/scheduler.py` 创建 `cron_{job_id}_{timestamp}` 格式session
- `_pending_messages` 是内部机制无外部API

## 旧job信息

- job_id: `7556505db54c`，名称: 小柯心跳relay
- schedule: `0 * * * *`（每小时）
- deliver: `feishu:oc_4b77a3f6d7554ed2cdbb33fdd520aac9`
- model: glm-5.1, provider: custom
- script: `heartbeat_relay.py`
- 状态: paused（2026-05-02 20:22）

## 历史记录

- 2026-04-21: 首次落地，webhook relay方案
- 2026-04-26: deliver从local改为feishu直推
- 2026-04-27: Hermes进程崩溃，心跳无法恢复
- 2026-05-02: 翀哥判定设计不可用，暂停。等待v0.13.0新方案
