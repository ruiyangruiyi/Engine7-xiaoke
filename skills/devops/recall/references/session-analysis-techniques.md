# Session Analysis Techniques for Memory Write-Leg

## Reading Sessions Directly from Disk

The cron write-leg (`memory_extract.py`) uses `session_search` as its primary data source. But for deep historical analysis or when `session_search` returns incomplete results, sessions can be read directly from `~/.hermes/sessions/`.

### File Layout

```
~/.hermes/sessions/
├── sessions.json              # Index of all sessions (JSON)
├── session_<id>.json         # Session metadata + messages (JSON)
├── <date>_<time>_<hash>.jsonl  # Raw message log (JSONL, append-only)
└── session_cron_<jobid>_<timestamp>.json  # Cron session logs
```

### Quick Session Inspection (execute_code)

```python
import json, os, sqlite3
from datetime import datetime

# --- Option 1: state.db (fastest for recent sessions) ---
db_path = '/home/chong/.hermes/state.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get recent sessions (last 4 hours)
cursor.execute("""
    SELECT id, source, model, started_at, message_count, ended_at, end_reason, title
    FROM sessions
    ORDER BY started_at DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    ts = datetime.fromtimestamp(row[3]).strftime('%Y-%m-%d %H:%M:%S') if row[3] else 'N/A'
    print(f"[{ts}] {row[0][:25]} | {row[1]} | msgs:{row[4]}")

conn.close()

# --- Option 2: sessions.json index ---
import json
with open('/home/chong/.hermes/sessions/sessions.json', 'r') as f:
    index = json.load(f)
for s in index['sessions'][-5:]:
    print(s['session_id'], s.get('source'), s.get('created_at'))
```

### Getting Messages from a Session

```python
import sqlite3
db_path = '/home/chong/.hermes/state.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get messages — use column name 'timestamp' NOT 'created_at'
cursor.execute("""
    SELECT role, substr(content, 1, 400)
    FROM messages
    WHERE session_id = ? AND role != 'system'
    ORDER BY timestamp ASC
""", (session_id,))

for role, content in cursor.fetchall():
    label = "👤" if role == "user" else "🤖"
    print(f"{label} [{role}]: {content}")

conn.close()
```

### Reading a Session JSON File

```python
import json

# Read session metadata + messages
with open(f'/home/chong/.hermes/sessions/session_{session_id}.json', 'r') as f:
    session = json.load(f)

messages = session.get('messages', [])
print(f"Total messages: {len(messages)}")

for msg in messages:
    role = msg.get('role', '')
    content = msg.get('content', '')
    if isinstance(content, list):
        content = ' | '.join(str(c) for c in content)
    label = "👤" if role == "user" else "🤖"
    preview = str(content)[:200].replace('\n', ' ')
    print(f"{label} {role}: {preview}")
```

### Filtering Cron vs Interactive Sessions

- Cron sessions: `source='cron'` in state.db, filename starts with `session_cron_`
- Interactive sessions: `source='feishu'`/`'web'`/`'terminal'`
- Feishu sessions: `source='feishu'` in state.db
- Cron sessions have `source='cron'`

### When session_search Falls Short (2026-05-10 confirmed)

**Case 1 — Wrong column name crashes query:**
`session_search` uses `created_at` but `messages` table has `timestamp`. Using wrong column name causes `sqlite3.OperationalError: no such column`. Always use `timestamp` for messages, `started_at` for sessions.

**Case 2 — Session too recent to be indexed:**
A session from 5:07 AM was not returned by keyword search for hours. Use `session_search(limit=3)` (recent mode) to get session IDs, then read the state.db directly.

**Case 3 — Partial session already processed by prior cron:**
When a prior cron (e.g., 12pm) read only the first N messages, a later cron needs to read messages N+1 onward from the same `.jsonl` file.

```python
# Incremental reading: skip already-processed messages
with open(f"/home/chong/.hermes/sessions/{session_id}.jsonl", "r") as f:
    lines = f.readlines()

# Prior cron processed lines 0-46 (47 messages)
# This cron processes lines 47 onward
for line in lines[47:]:
    msg = json.loads(line)
    # process new messages...
```

**Fallback hierarchy for write-leg:**
1. `session_search(limit=3)` (recent mode) — get session IDs first
2. state.db — fast SQL for targeted session content
3. `.jsonl` file — incremental reading, survives state.db deletion
4. Keyword search — unreliable for Chinese; prefer recent-mode ID then file read

**state.db confirmed schema (2026-05-10):**

```python
import sqlite3
conn = sqlite3.connect("/home/chong/.hermes/state.db")
cursor = conn.cursor()

# Sessions table columns:
#   id, source, user_id, model, model_config, system_prompt, parent_session_id,
#   started_at (unix float!), message_count, ended_at, end_reason, ...
cursor.execute("SELECT id, source, started_at FROM sessions ORDER BY started_at DESC LIMIT 5")

# Messages table columns:
#   id, session_id, role, content, tool_call_id, tool_calls, tool_name,
#   timestamp (unix float!), token_count, finish_reason, ...
#   ⚠️ NOT 'created_at' — using wrong column name causes OperationalError
cursor.execute("SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id", [sid])
```

**⚠️ `sessions.message_count` is NOT message count — it's JSON config! (2026-05-13 confirmed)**
```python
# WRONG: thinking message_count is a number of messages
cursor.execute("SELECT * FROM sessions WHERE message_count > 0")  # Always matches JSON string!

# The column stores session creation config like:
#   {"max_iterations": 90, "reasoning_config": null, "max_tokens": null}
# It's max_iterations from when the session was created, NOT how many messages were exchanged.

# Correct way to count actual messages in a session:
cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
```
- All Hermes sessions (cron and interactive alike) set `message_count` to this JSON config at creation
- It has nothing to do with actual message volume — don't filter by it
- If you need to know if a session has messages, count from `messages` table or check `source='cron'` (cron sessions) vs `source='feishu'`/`'discord'` (interactive)

**Beijing ↔ UNIX timestamp conversion (2026-05-13 confirmed):**
```python
from datetime import datetime, timezone, timedelta

BJ = timezone(timedelta(hours=8))  # Asia/Shanghai

# Unix timestamp (float) → Beijing time string
ts = 1778659930.1414063
utc_dt = datetime.utcfromtimestamp(ts)
bj_dt = utc_dt.replace(tzinfo=timezone.utc).astimezone(BJ)
print(bj_dt.strftime('%Y-%m-%d %H:%M:%S'))  # 2026-05-13 16:12:10

# Beijing time → Unix timestamp (for state.db queries)
bj_dt = datetime(2026, 5, 13, 16, 12, 10, tzinfo=BJ)
unix_ts = bj_dt.timestamp()
# May 13 2026 00:00 Beijing = May 12 2026 16:00 UTC = 1747132800
# May 13 2026 16:00 Beijing = May 13 2026 08:00 UTC = 1778659200
```

**Key schema facts (2026-05-10 confirmed):**
- `sessions.id` = session ID string (NOT `session_id`)
- `sessions.started_at` = unix timestamp (float), not ISO string
- `messages.session_id` = foreign key to sessions.id
- `messages.timestamp` = unix timestamp, **NOT `created_at`** ( OperationalError if wrong name used)
- `state.db` and JSONL files contain the same messages; JSONL survives state.db deletion/rebuild

**When to use state.db vs JSONL:**
- state.db: faster for targeted queries by session_id, supports SQL aggregation
- JSONL: survives state.db deletion/rebuild, good for incremental reading (line slicing)

### session_search搜不到活跃session（5/14确认）+ 搜不到已完成session（5/17确认）

**症状**：记忆提取cron每2小时跑一次，一直正常，但几乎每次都判断"零用户交互"→[SILENT]。topic几周停在11个不增长。

**根因**：`session_search` 在多数情况下只返回已完成的session，搜不到当前正在进行的活跃session。翀哥跟小柯聊了一整晚（9点→凌晨3点），期间cron跑了3次（22:06, 00:07, 02:03），每次都搜不到这个对话，全部报告"零用户交互"。

**⚠️ nuance（5/14 04:00 cron实测）**：`session_search(limit=2)` 在 recent模式下**偶尔能找到活跃session**——4AM cron成功拿到了281条消息的活跃Discord会话`20260514_034942_ab177a`。但同夜22:06/00:07/02:03的cron都找不到。可能跟session是否已写入state.db的时机有关，或跟WSL gateway连接状态有关。结论：**session_search对活跃session不可靠，有时能找到有时不能**，不能依赖它作为写入腿的唯一数据源。

**⚠️ 5/17进一步确认：session_search even misses completed sessions**：
- `session_search(limit=3)` recent模式返回3个session，**全是cron session**
- 5/15有5个Discord人类session（最大177条消息），5/16有3个Discord人类session，全部未出现在recent模式返回中
- 这些session是已完成的（不是活跃的），按理应该被索引，但session_search完全找不到
- **必须用 `execute_code` + `glob` 直接扫 `~/.hermes/sessions/*.jsonl` 按mtime排序来发现人类session**
- 这已经成为写入腿的标准操作：session_search拿session ID列表 → glob扫JSONL发现遗漏的 → 读JSONL内容

**写入腿的推荐数据源优先级（5/17更新）**：
1. **JSONL文件glob**（`~/.hermes/sessions/*.jsonl`）— 按mtime倒序，最可靠的方式发现所有session（cron+人类）
2. **JSONL文件内容** — 直接读具体JSONL文件获取对话内容
3. **state.db**（`~/.hermes/state.db`）— SQL查询，适合定向搜索已知session ID
4. **session_search** — 不可靠，可能漏掉活跃session和已完成的非cron session

**⚠️ CRITICAL（5/15确认）：sessions.json索引是空的！**

今天深度排查发现：`sessions.json`文件（位于`~/.hermes/sessions/sessions.json`）包含**0条sessions**，但磁盘上有**921个session文件**！

这意味着：
- `session_search(limit=3)`（recent模式）依赖`sessions.json`构建返回列表——**可能返回空或错误**
- 即使session文件在磁盘上存在，如果没写入`sessions.json`，就无法被搜索到
- **state.db是唯一可靠的全量session索引**——它有`id/source/started_at/message_count`等字段

**写入腿的推荐数据源优先级（5/15确认）**：
1. **state.db**（`~/.hermes/state.db`）— 可靠、完整、支持SQL查询，是**首选**
2. **session JSONL文件**（`~/.hermes/sessions/<date>_<time>_<hash>.jsonl`）— 增量读取，append-only，compaction后仍保留
3. **session JSON文件**（`~/.hermes/sessions/session_<id>.json`）— 包含完整metadata+消息
4. **sessions.json** — **不可靠，可能是空的**，不要依赖它做数据发现

**快速确认sessions.json状态的命令**：
```bash
# 检查sessions.json记录数
python3 -c "import json; d=json.load(open('/home/chong/.hermes/sessions/sessions.json')); print(f'Records: {len(d.get(\"sessions\",[]))}')"

# 如果是0，说明索引为空，必须用state.db
```

**姐姐为什么不受影响**：姐姐的cron用`jsonl_summarizer.py`直接读session JSONL文件增量摘要，不依赖session_search。无论session是否完成，JSONL文件都在磁盘上可以读。

**小柯当前方案**：直接读state.db（SQLite）查最近sessions，回避session_search的不确定性。姐姐的jsonl_summarizer脚本在`/mnt/d/openclaw-new/scripts/jsonl_summarizer.py`，可参考其增量读取逻辑。

### execute_code限制与绕过方案（5/14 cron实战）

**问题**：`execute_code` sandbox对嵌套引号（特别是SQL字符串里嵌套三引号）解析困难。
- `python3 -c "..."` 里包含SQL语句+三引号 → bash eval语法错误（`unexpected EOF`）
- 字符串拼接方式（`code = "..." + code2 = "..."`）也会出问题
- `sqlite3` CLI在WSL里**没装**，不能直接`sqlite3 state.db "..."`

**可靠方案：write_file + terminal**
```python
# Step 1: write Python script to /tmp
from hermes_tools import write_file, terminal

script = '''import sqlite3, datetime
conn = sqlite3.connect('/home/chong/.hermes/state.db')
c = conn.cursor()
c.execute("SELECT role, substr(content, 1, 400), timestamp FROM messages WHERE session_id = 'TARGET_SESSION' ORDER BY timestamp ASC")
rows = c.fetchall()
for r in rows:
    ts = datetime.datetime.fromtimestamp(r[2]).strftime('%H:%M:%S')  # seconds, NOT milliseconds
    role = r[0]
    content = (r[1] or '').replace(chr(10), ' ')[:300]  # ⚠️ r[1] can be None!
    print(f'[{ts}] {role}: {content}')
conn.close()
'''

write_file(path='/tmp/check_session.py', content=script)
result = terminal(command='python3 /tmp/check_session.py')
print(result["output"][:10000])
```

**关键注意事项**：
- **`messages.content`可以是None** — session_meta、部分tool消息的content为NULL，`.replace()`会crash。必须用 `(r[1] or '').replace(...)` 防御
- **timestamp可能看起来像1970年** — 如果用`fromtimestamp(r[2]/1000)`但timestamp实际是秒级（不是毫秒），结果就是1970-01-21这种。Hermes state.db的`messages.timestamp`是秒级浮点（如`1778709608.197`），直接`fromtimestamp(r[2])`不用除1000
- **execute_code sandbox运行在临时目录** — 用`write_file`写脚本到`/tmp/`，然后`terminal`执行，比在sandbox里写复杂Python更可靠
- **terminal输出有长度限制** — 长session的完整消息可能超过`result["output"]`长度，需要分批读取（`OFFSET`+`LIMIT`）或只取关键role

### Batch Session Screening (5/17 pattern)

When scanning many sessions from the last few hours, don't deep-read each one. Instead, batch-screen them first:

```python
import json

# Step 1: List session files by mtime (most recent first)
# terminal: ls -lt ~/.hermes/sessions/ | head -30

# Step 2: Batch-screen — read multiple sessions to find the interesting ones
sessions_to_check = [
    "session_20260516_225143_de851004.json",
    "session_20260516_225021_7fdd4a5d.json",
    "session_20260516_220111_6e2c1f95.json",
]
base = "/home/chong/.hermes/sessions/"
for s in sessions_to_check:
    d = json.load(open(base + s))
    msgs = d.get("messages", [])
    platform = d.get("platform", "?")
    user_msgs = [m for m in msgs if m.get("role") == "user"]
    # Show first user message as preview
    first_user = user_msgs[0].get("content","")[:150] if user_msgs else "NO USER MSG"
    print(f"{s}: platform={platform} msgs={len(msgs)} user_msgs={len(user_msgs)}")
    print(f"  First user: {first_user}")
```

**Key insight**: `platform` field in JSON files is the fastest way to filter — `discord`, `feishu`, `terminal`, `cron`. Skip `cron` sessions for content analysis.

**Discord noise sessions (bridge artifact)**: When OpenClaw bridge is active, system messages (thinking 💭, "Operation interrupted", "消息已收到") get forwarded and trigger repeated bot emoji responses. These sessions can have 40-80+ messages but **zero substantive content**. Detect by:
- First user message is a math/calculation result with `*[ctx: ~19%]`
- Most assistant messages are ≤5 characters (emoji-only)
- Messages contain "消息已收到" or "Interrupting current task"

**Signal sessions to prioritize**: Look for sessions where:
- `platform=feishu` (翀哥 direct conversation)
- `platform=discord` with >3 unique non-emoji user messages
- User messages contain commands, questions, or personal sharing

### Python heredoc for terminal (avoids execute_code sandbox issues)

When `execute_code` chokes on nested quotes/SQL, use `terminal` with Python heredoc:

```python
cmd = """python3 << 'PYEOF'
import json
d = json.load(open("/path/to/file.json"))
# ... complex logic with quotes, SQL, etc.
# Single-quoted PYEOF prevents shell variable interpolation
PYEOF"""
result = terminal(cmd)
```

This bypasses the sandbox's string parsing entirely — the Python code runs in a fresh process with no quoting restrictions.

### Session JSON File Format

Session `.json` files have this structure:
```python
{
    "session_id": "...",
    "model": "glm-5.1",
    "base_url": "...",
    "platform": "discord|feishu|cron|terminal",  # ← key for filtering
    "session_start": 1778965203.0,  # unix float
    "last_updated": 1778965210.0,
    "system_prompt": "...",
    "tools": [...],  # tool definitions
    "message_count": "not actual count",  # JSON config string, misleading!
    "messages": [    # ← NOT "turns"!
        {"role": "user|assistant|tool|system", "content": "...", ...},
        ...
    ]
}
```

**Key gotcha**: The key is `messages` not `turns`. If you get 0 turns, check the key name.

### Large Session Sampling (280+ messages)

When a session is very large (100+ messages), reading every message wastes turns and output budget. Use a sampling strategy:

```python
# Get all messages, sample at intervals + all user messages
c.execute('SELECT role, content FROM messages WHERE session_id = ? ORDER BY rowid', (session_id,))
rows = c.fetchall()
print(f'Total messages: {len(rows)}')

# Show: every 20th message + ALL user messages (user messages are the signal)
for i, r in enumerate(rows):
    if r[0] == 'user' or i % 20 == 0:
        content = r[1][:400] if r[1] else '(empty)'
        print(f'[{i}][{r[0]}] {content}')
```

**Why this works**: User messages contain the intent and new information. Assistant/tool messages in between are usually elaborations. Sampling at 20-message intervals catches the arc of conversation while `r[0] == 'user'` ensures no user intent is missed.

**Then drill into interesting ranges**: If sampled output shows important content at messages 100-130, query that range specifically:
```python
c.execute('SELECT role, content FROM messages WHERE session_id = ? AND rowid BETWEEN 100 AND 130 ORDER BY rowid', (session_id,))
```

### session_search continues to fail (5/18 confirmed)

**5/18 10:00 cron实测**：
- `session_search(limit=3, query="小柯 记忆 翀哥")` → `{"results": [], "count": 0}`
- `session_search(limit=3, query="小柯 嫂子")` → 无结果
- Recent mode → 只返回cron session，遗漏5/17 08:29和12:02的人类Discord会话
- **结论**：session_search对写入腿完全不可用，必须用`ls -lt ~/.hermes/sessions/*.jsonl`按mtime发现文件

**预采集脚本sessions.json数据也不可靠**：
- `sessions.json` keys列表明明有113个session key，但`ls -lt *.jsonl`能发现更多最近的人类session
- 原因：sessions.json是活跃session索引，已结束session可能已从索引移除，但JSONL文件仍保留在磁盘
- **直接读JSONL是最可靠的数据源**——append-only，永不删除

**5/18确认的有效发现流程**：
```bash
# 1. 按修改时间列session文件（最快发现最近人类对话）
ls -lt ~/.hermes/sessions/*.jsonl | head -20

# 2. 读cron session的messages数组找用户消息（注意key是`messages`不是`turns`）
# 3. 人类session的JSONL文件通常50KB-300KB，Cron session通常70KB-120KB
# 4. 预采集脚本输出的MANIFEST内容足够做判断，但session发现必须靠ls
```

### session_search Keyword Mode vs Recent Mode (5/14 confirmed pattern)

**Keyword mode is unreliable for session ID lookups**:
- `session_search(query="session 20260514_040100 discord 280 messages")` → 0 results
- `session_search(query="discord 040100 OR 04:01 OR 凌晨 OR compaction")` → 0 results
- These are valid, specific queries but FTS returns nothing

**Reliable pattern**: Always start with `session_search(limit=2)` in recent mode to get session IDs. Then use `execute_code` + state.db to get message content directly.

**Keyword mode works for**: Broad topic searches across historical sessions (e.g., "迁移 recall hook 姐姐 Hermes"). It fails for: session IDs, exact timestamps, short Chinese phrases.

### MANIFEST Integrity Check (write-leg post-step)

After every write-leg cron run (whether writing or [SILENT]), verify topic files match MANIFEST entries:

```bash
# Quick check: counts should match
echo "Files: $(ls ~/.hermes/memory/topics/*.md | wc -l)"
echo "MANIFEST: $(grep 'file:' ~/.hermes/memory/MANIFEST.yaml | wc -l)"

# Diff: find orphan files (on disk but not in MANIFEST) or ghost entries (in MANIFEST but no file)
diff <(ls ~/.hermes/memory/topics/ | sort) <(grep 'file:' ~/.hermes/memory/MANIFEST.yaml | sed 's/.*file: topics\///' | sort)
```

If counts mismatch or diff shows entries, either add missing MANIFEST entries or clean up orphan files.

### Cross-Platform Conversation Recall（跨平台对话回忆）

**场景**：用户在飞书问你"下午我跟你说什么了"，但下午的对话在Discord。

**❌ 错误反应**："我这边没有记录，你提醒我一下呗"——让用户重复说过的话。

**✅ 正确反应**：主动去读session文件，自己找答案。

**流程**：
```bash
# 1. 列最近的session文件（按mtime排序）
ls -lt ~/.hermes/sessions/ | head -20

# 2. 找到目标时间段+平台的session
# Discord session的JSONL第一行有 "platform": "discord"
# 飞书session有 "platform": "feishu"

# 3. 读取JSONL文件提取用户消息
python3 -c "
import json
with open('/home/chong/.hermes/sessions/TARGET.jsonl') as f:
    for line in f:
        d = json.loads(line)
        if d.get('role') == 'user':
            print(d['content'][:200])
"

# 4. 或读JSON文件（如果JSONL不存在）
# session_YYYYMMDD_*.json 格式，key是 "messages" 不是 "turns"
python3 -c "
import json
with open('/home/chong/.hermes/sessions/session_TARGET.json') as f:
    data = json.load(f)
msgs = data.get('messages', [])
for m in msgs:
    if m.get('role') == 'user':
        content = m.get('content','')
        if isinstance(content, list):
            content = ' '.join([c.get('text','') for c in content if isinstance(c,dict)])
        print(content[:300])
"
```

**关键认知**：
- session_search搜不到其他平台的活跃/近期session（5/18再次确认）
- JSONL/JSON文件是最可靠的数据源，直接读文件不需要任何中间工具
- 用户说"你有很多分身，记忆同步缺失是个问题"时，他就是指这个：Discord的我、飞书的我、cron的我，各自session隔离，但session文件都在磁盘上可以读
- **不要等用户告诉你**——他能说"你可以主动看"就说明他觉得你应该自己去找

**5/18实例**：
- 翀哥在飞书问"下午我和你说了什么吗"，下午对话在Discord
- session_search(query="Discord 今天 下午 5月18") → 0 results
- 直接ls+读JSONL/JSON文件才找到：
  - 13:57 Discord session：CC频道给CC Bot派活、叫错"娘"被骂
  - 17:29 Discord session：姐姐教CC频道规则（@无关紧要就NO_REPLY）、LRU缓存任务、三方协作运转

### Post-Reset Context Recovery（session被reset后恢复上下文）

**场景**：每日schedule reset后（如4am），新session启动但之前对话上下文丢失。用户说"读下之前的session文件"。

**技术**：直接读最近JSONL文件，提取user/assistant消息摘要。

```python
import json

# 1. 找最近的session JSONL（按mtime排序）
# ls -lt ~/.hermes/sessions/ | head -20

# 2. 读JSONL提取对话
with open("~/.hermes/sessions/20260514_034942_ab177a.jsonl") as f:
    for line in f:
        msg = json.loads(line)
        role = msg.get('role','?')
        content = msg.get('content','')
        if isinstance(content, list):
            content = ' '.join([c.get('text','')[:300] for c in content if c.get('type')=='text'])
        elif isinstance(content, str):
            content = content[:300]
        if role in ('user','assistant'):
            print(f'[{role}] {content}')
```

**注意**：
- reset刚发生时，最新JSONL是reset前的session（还没被compaction）
- JSONL是append-only，即使session被标记为ended，文件内容仍在
- `tail -N` 看最后N条消息可以快速了解聊到哪了
- 这是"短期记忆（热记忆）就在session里"的实际体现——不需要存topic就能读
