# Hermes Session Architecture (Source Code Reference)

From `gateway/session.py` (1387 lines) and `gateway/config.py`.

## SessionEntry Fields

| Field | Type | Purpose |
|-------|------|---------|
| `session_key` | str | Deterministic key from message source |
| `session_id` | str | `YYYYMMDD_HHMMSS_<8hex>` — unique per session |
| `created_at` / `updated_at` | datetime | Timestamps |
| `origin` | SessionSource | Where messages come from (platform, chat_id, user_id, etc.) |
| `was_auto_reset` | bool | True when session was auto-reset (idle/daily policy) |
| `is_fresh_reset` | bool | True after manual `/new` or `/reset` |
| `suspended` | bool | Hard wipe flag (from `/stop` or stuck-loop) |
| `resume_pending` | bool | Set on graceful restart; preserves session_id |
| `expiry_finalized` | bool | Set by background watcher after session expiry cleanup |

## SessionStore Methods

| Method | What it does |
|--------|-------------|
| `get_or_create_session(source)` | Main entry — evaluates reset policy, returns or creates SessionEntry |
| `update_session(session_key)` | Updates `updated_at` timestamp |
| `reset_session(session_key)` | Force reset — new session_id, same key |
| `switch_session(session_key, target_id)` | Resume a specific old session |
| `suspend_session(session_key)` | Mark for hard wipe on next access |
| `mark_resume_pending(session_key)` | Mark for graceful restart recovery |
| `prune_old_entries(max_age_days)` | Drop old session_key mappings |
| `suspend_recently_active(max_age_seconds)` | Called on startup after crash/restart |

## SessionSource Fields

| Field | Purpose |
|-------|---------|
| `platform` | Platform enum (DISCORD, TELEGRAM, FEISHU, etc.) |
| `chat_id` | Channel/group/DM identifier |
| `chat_type` | "dm", "group", "channel", "thread" |
| `user_id` | Sender identifier |
| `thread_id` | For forum topics, Discord threads |
| `guild_id` | Discord guild / Slack workspace |
| `is_bot` | True when message author is a bot |

## Reset Policy Resolution

```
get_reset_policy(platform, session_type):
  1. Check reset_by_platform[platform]
  2. Check reset_by_type[session_type]
  3. Fall back to default_reset_policy
```

## Session Key Isolation Rules

- DMs: always isolated per chat_id (each private conversation = own session)
- Groups: isolated per user when `group_sessions_per_user: true` (default)
- Threads: SHARED by default (all participants in one session), unless `thread_sessions_per_user: true`

## Config Reference

```yaml
# In config.yaml
session_reset:
  mode: both           # none | idle | daily | both
  idle_minutes: 1440   # default 24h
  at_hour: 4           # default 4am local time

# Per-platform override
gateway:
  reset_by_platform:
    discord:
      mode: idle
      idle_minutes: 4320

# Per-type override  
  reset_by_type:
    dm:
      mode: idle
      idle_minutes: 100000
```

## Files on Disk

```
~/.hermes/sessions/
├── sessions.json          # session_key → SessionEntry mapping
├── *.jsonl                # (legacy) session transcripts  
└── state.db               # SQLite: sessions table + messages + FTS5 index
```

## Useful CLI Commands

```bash
hermes sessions list            # List recent sessions
hermes sessions browse          # Interactive picker
hermes sessions stats           # DB size, session count, message count
hermes sessions prune --older-than 7  # Clean up old entries
hermes sessions rename ID TITLE # Name a session
hermes sessions delete ID       # Delete a session
```
