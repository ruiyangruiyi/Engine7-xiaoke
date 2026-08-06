# Hermes Session/JSONL 加载机制（2026-05-27研究）

研究目的：为OpenClaw Engine Phase 4+ session实现提供参考。

## 存储架构：双写

每次对话消息同时写两份：
1. **SQLite**（`SessionDB`）— 新格式，支持FTS5搜索
2. **JSONL**（`{session_id}.jsonl`）— 老格式，每行一条JSON，append-only

### 双写原因
- SQLite是后加的存储层（过渡期）
- 老session只有JSONL，迁移后SQLite可能只有部分消息
- 双写保证过渡期不丢数据

## 加载逻辑：取多的那份

`load_transcript()` 源码位置：`gateway/session.py:1303`

```python
def load_transcript(self, session_id: str) -> List[Dict[str, Any]]:
    # 1. 先从SQLite读
    db_messages = self._db.get_messages_as_conversation(session_id)
    
    # 2. 再从JSONL读（老session可能更多）
    jsonl_messages = []  # 逐行JSON parse
    
    # 3. 哪个消息多用哪个
    if len(jsonl_messages) > len(db_messages):
        return jsonl_messages
    return db_messages
```

**关键设计**：取多的那份，防止迁移期老session的JSONL比SQLite消息多时被截断。

## 重启后加载流程

```
gateway重启 → 用户发消息 → get_or_create_session()
  → load_transcript(session_id)
  → 全量加载（SQLite或JSONL，哪个多取哪个）
  → 整个塞给conversation_history → 传给模型
```

**没有取舍！** 全量加载，一股脑塞给模型。

## "取舍"在哪——Session Hygiene（自动压缩）

全量加载后如果太大（`gateway/run.py:6349-6515`）：

### 触发条件
1. **估算token** ≥ context window的85%（hygiene阈值比agent自己的50%高）
2. **消息数** ≥ 400条硬上限（`hygiene_hard_message_limit`）
3. 消息数 ≥ 4条才检查（避免空session误触发）

### Token估算
- 优先用上次API返回的 `prompt_tokens`（准确）
- fallback用 `len(msg)//4` 粗估（高估30-50%，但安全）

### 压缩过程
1. 触发 `/compact` — 用小模型把历史总结成一条system message
2. `rewrite_transcript()` — **整个覆写JSONL**，只保留压缩后的摘要
3. **不可逆**——原文被覆盖，无法恢复

### 配置
```yaml
# config.yaml
compression:
  enabled: true
  hygiene_hard_message_limit: 400  # 消息数硬上限
```

## 对OpenClaw Engine的启发

### 现状（Phase 4）
- Engine有JSONL写入（SessionWriter）
- 恢复时全量加载 → 硬截断（RESTORE_MAX_MESSAGES=100, 50K token）
- 没有智能压缩

### 可改进方向
1. **分级取舍**：按消息类型分级——tool调用结果压缩、情感对话保留原文
2. **摘要+原文共存**：压缩时不覆盖原文，另存摘要，需要时回溯
3. **Token预算**：给每个session分配token预算，重要消息占预算多
4. **参考姐姐的topic-recall**：不是全量塞context，而是按需召回相关topic
