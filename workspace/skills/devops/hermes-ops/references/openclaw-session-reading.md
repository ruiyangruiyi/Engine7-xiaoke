# Reading OpenClaw Agent Chat History

## Which Project Directory

| Version | Config/State Directory | Port | Status |
|---------|----------------------|------|--------|
| v4.11 (old, stable) | `/mnt/c/Users/24045/.openclaw/` | 16888 | ⚠️ DO NOT use for reading recent chats |
| v2026.5.3+ (new) | `/mnt/c/Users/24045/.openclaw-new/` | 16688 | ✅ Use this for current chat data |

**Key correction (5/13):** 翀哥明确说"翻新的别翻旧项目" — always use `.openclaw-new/` for current data.

**Source code** is on D drive: `/mnt/d/openclaw-new/` — NOT in the config directory.

## Session File Structure

```
.openclaw-new/agents/{agent_id}/sessions/
├── sessions.json                          # Session metadata index
├── {uuid}.jsonl                           # Active session transcript
├── {uuid}.trajectory.jsonl                # Agent reasoning/planning trace
├── {uuid}.trajectory-path.json            # Trajectory path metadata
├── {uuid}.jsonl.bak-{size}-{timestamp}    # Backup snapshots
├── {uuid}.checkpoint.{id}.jsonl           # Checkpoint snapshots
└── {uuid}.jsonl.deleted.{timestamp}       # Soft-deleted sessions
```

**Agent IDs:**
- `main` — 张小欧 (main agent)
- `mkt` — 张小媒/姐姐 (CEO agent)

## JSONL Format

Each line is a JSON object with a `type` field:

```json
{"type":"session","version":3,"id":"uuid","timestamp":"...","cwd":"..."}
{"type":"message","id":"msg-uuid","parentId":"...","timestamp":"...","message":{...}}
```

### Message Entry Structure

```json
{
  "type": "message",
  "id": "ea060b56-...",
  "parentId": "ea060b56-...|null",
  "timestamp": "2026-05-13T12:53:04.192Z",
  "message": {
    "role": "user|assistant",
    "content": [
      {"type": "text", "text": "actual message text"}
    ],
    "api": "openai-responses",
    "provider": "openclaw|openclaw-mirror",
    "model": "delivery-mirror|glm-5.1|...",
    "usage": {"input":0,"output":0,...},
    "stopReason": "stop",
    "timestamp": 1778503984150,
    "idempotencyKey": "msg-send-..."
  }
}
```

**Content formats:**
- **List** (most common): `[{"type":"text","text":"..."}]` — extract with `[c["text"] for c in content if c.get("type") == "text"]`
- **String** (rare): just plain text
- **Voice markers**: `{"type":"text","text":"--voice"}` indicates a voice message attachment

### Special Message Types

- **User messages** with `[Wed 2026-05-13 19:23 GMT+8]` prefix — timestamp injected by platform
- **Heartbeat triggers**: `"【定时心跳】请 read HEARTBEAT.md 并按其中的流程执行。..."` — cron-injected, can filter out
- **Delivery mirror**: `provider: "delivery-mirror"` with 0 usage — messages relayed from another session/channel

## Reading Strategy

### Find Active Sessions

```bash
# List most recent sessions (by modification time)
ls -lt /mnt/c/Users/24045/.openclaw-new/agents/mkt/sessions/*.jsonl | head -5

# Find the largest/most recent active session (likely the main conversation)
ls -ltS /mnt/c/Users/24045/.openclaw-new/agents/main/sessions/*.jsonl | head -5
```

### Extract Conversation (via execute_code)

```python
import json

lines = open("path/to/session.jsonl").readlines()
for line in lines:
    d = json.loads(line.strip())
    if d.get("type") == "message":
        msg = d.get("message", {})
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            if isinstance(content, list):
                text = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            else:
                text = str(content)
            # Filter out heartbeat noise
            if "【定时心跳】" in text or text.strip() == "--voice":
                continue
            print(f"[{role}] {text[:300]}")
```

### Quick Scan Last N Messages (via terminal)

```bash
tail -100 '/path/to/session.jsonl' | python3 -c "
import json, sys
for line in sys.stdin:
    d = json.loads(line.strip())
    if d.get('type') == 'message':
        msg = d['message']
        role, content = msg.get('role',''), msg.get('content','')
        if role in ('user','assistant') and content:
            text = content if isinstance(content, str) else ' '.join(c.get('text','') for c in content if isinstance(c,dict))
            if '定时心跳' not in text: print(f'[{role}] {text[:200]}')
"
```

⚠️ Note: `cat | python3` pattern may be blocked by security scan. Use `execute_code` tool or `read_file` + inline parsing instead if blocked.

## Pitfalls

- **Old project has only deleted/stale sessions** — the `.openclaw/` (v4.11) mkt agent sessions are all `.deleted` files from May 5 and earlier. Always check `.openclaw-new/` for current data.
- **Session files can be very large** (7+ MB for main agent) — use `tail` to read only the end, or filter by role to avoid processing megabytes of data.
- **Heartbeat noise** — cron injects heartbeat messages every 15-30 minutes, which dominate the transcript. Filter out lines containing `【定时心跳】` and `HEARTBEAT_OK` when scanning for actual conversation.
- **Backup files** — `.bak-*` and `.checkpoint.*` files are snapshots, not active sessions. Read the plain `.jsonl` file for current data.
- **`delivery-mirror` provider** — messages with this provider and 0 token usage are relayed from another channel/session, not generated in this session.
