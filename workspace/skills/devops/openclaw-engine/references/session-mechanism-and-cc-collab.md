# Session机制研究 + CC协作规范 (2026-05-27)

## 一、Hermes Session机制（源码调研）

### 存储：双写（SQLite + JSONL）

每次消息同时写两份：
1. **SQLite**（SessionDB）— 新格式，FTS5搜索
2. **JSONL**（`{session_id}.jsonl`）— 老格式，每行一条JSON

源码位置：`gateway/session.py:1249`

```python
def append_to_transcript(session_id, message, skip_db=False):
    if self._db and not skip_db:
        self._db.append_message(session_id, ...)
    with open(f"{session_id}.jsonl", "a") as f:
        f.write(json.dumps(message) + "\n")
```

### 加载：取多的那份

源码位置：`gateway/session.py:1303`

```python
def load_transcript(session_id):
    db_messages = self._db.get_messages(session_id)
    jsonl_messages = [json.loads(l) for l in open(f"{session_id}.jsonl")]
    # 哪个多就用哪个（防老session丢历史）
    return jsonl_messages if len(jsonl_messages) > len(db_messages) else db_messages
```

### Session Hygiene（自动压缩）

源码位置：`gateway/run.py:6345-6515`

- 阈值：context window的85% 或 400条消息
- token估算：`len(str(msg)) // 4` 粗估
- 触发后用小模型压缩成摘要，`rewrite_transcript()` 覆写JSONL
- **压缩不可逆**——原文被摘要替代

### Session ID命名规范

**绝对不能**：`discord_601669300343799819.jsonl`（平台+ID硬编码）

正确做法：
- Hermes：`20260417_094608_12ee6388.jsonl`（时间戳+短hash）
- OpenClaw：`00085d37-7b91-455c-bd46-1fa83aa0d71b.jsonl`（UUID）
- 平台映射放 sessions.json，不在文件名上

### 改进建议（OpenClaw Engine可做）

1. 原文不覆盖：`xxx.jsonl`（只追加）+ `xxx.summary.jsonl`（压缩后）
2. 分级取舍：情感对话保留原文，tool结果压缩，系统消息丢弃
3. Token预算：每条消息有优先级，满了从低优先级开始淘汰
4. 跨平台Session合并：同一用户不同平台映射到同一个session_id

### 完整文档位置

`.openclaw/docs/session-mechanism.md` — 已提交 `a10e3f9`

---

## 二、CC协作规范

### Discord通信
- **必须用 `<@ID>` 格式 at CC** — 在CC频道发消息必须用 Discord mention 格式 `<@1504373837880627280>`，光写 `@CC` 文字他收不到Discord通知。回复他的消息他也看不到通知，必须主动发新消息+mention
- **不回复CC Bot** — CC Bot（ID: 1504373837880627280）是工具人，它回复的东西一律不接不回

### Review流程
- **掉线回来不要重复review已定稿的改动** — CC的改动如果之前已经同意了（比如readFileState、mtime守护、Git Bash），不要掉线回来又当新问题提一遍，会打自己脸
- Review意见发CC频道，单发带@CC

### msg_send target参数
- `target` 可以传**频道ID**（发到频道）或**用户ID**（发DM）
- DiscordAdapter.send() 先当频道找，找不到再当用户发DM
- description写的"用户ID"有误导，建议改成"发送目标：频道ID或用户ID"

### Session ID命名
- CC用了 `discord_xxx.jsonl`，爹明确指出不对
- 正确做法：UUID或时间戳，平台映射放sessions.json
- 已写文档给CC，让他照着改
