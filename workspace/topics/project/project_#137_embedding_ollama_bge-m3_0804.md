---
name: #137 EverOS embedding 切 ollama bge-m3——提前闭环
description: 2026-08-04 晚 #137 提前完成——embedding 已切 ollama bge-m3、363 episodes 重 embed 完成、memory_search top score 1.000 验证通过
type: project
date: 2026-08-04
---

2026-08-04 晚 #137「EverOS embedding 切本地 ollama bge-m3」**提前闭环，标 done**。

**完成链路**：
- Docker VM 内存调到 8GB → bge-m3 装得下
- cascade worker 跑稳 → md_change_state.upsert 重置 status 回 pending → episode 全部重新 embed
- 363 episodes 已重嵌入，search 实测 top score 1.000（之前默认指向 DeepInfra 远程 API 空 key 搜不到的根本问题彻底解决）
- 之前 OME 的 episode extraction 0 行、import 脚本 skip flush 等问题全部顺带闭环

**Why:** 这条线串起了 8/4 一整天的 5 层根因（Docker VM 内存 / cascade worker 不重试 / embedding 默认配错 / OME 不自动跑 / import 跳过 flush）—— 修完 #137 这五条一次性收齐。

**How to apply:**
1. EverOS memory_search 不再是问题，外部群/新用户装机直接走 embedding=bge-m3 路线
2. 默认配置再 review 一次，确认没有其他项还是 DeepInfra 远程 API（key 仍是空）
3. bge-m3 embed 时间预期：CPU 5-20s/条，单条短 query <1s——别再误判"又卡住"
4. cascade worker 的 OME retry 限制仍存在，未来新 episode 进来还是得靠 md_change_state 手动 touch 触发

**8/4 状态**：#137 标 done，EverOS embedding/search 链全通；后面可以放心接 #131/#75 等其他 task 了。