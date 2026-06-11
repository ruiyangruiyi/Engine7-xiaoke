# Shell Hooks Debug Notes (5/10 session)

## Problem: pre_llm_call hook registered but not injecting context

### Symptoms
- `hermes hooks doctor` showed hook healthy (exists, executable, allowlisted, valid JSON)
- `agent.log` showed hook registered at startup but **no execution traces** during messages
- Agent could not see any `<system-reminder>` recall context

### Root Cause 1: `user_message` in `extra` dict

`agent/shell_hooks.py` line 360 defines `_TOP_LEVEL_PAYLOAD_KEYS = {"tool_name", "args", "session_id", "parent_session_id"}`. The `_serialize_payload()` function (line 468) puts everything else into `extra`:

```python
extras = {k: v for k, v in kwargs.items() if k not in _TOP_LEVEL_PAYLOAD_KEYS}
payload = {
    "hook_event_name": event,
    "tool_name": kwargs.get("tool_name"),
    "tool_input": kwargs.get("args"),
    "session_id": kwargs.get("session_id"),
    "cwd": cwd,
    "extra": extras,  # <-- user_message ends up here
}
```

So the stdin JSON looks like:
```json
{"hook_event_name":"pre_llm_call","tool_name":null,"tool_input":null,"session_id":"...","cwd":"...","extra":{"user_message":"the actual message","is_first_turn":true,...}}
```

Hook script must read `d['extra']['user_message']`, not `d['user_message']`.

### Root Cause 2: recall_v2.py returns non-empty when no match

When recall_v2 finds no matching topics, it outputs:
```
[recall v2] glm-4.7 fallback selected: []
Query: ...

No matching topics found.
```

This is non-empty text, so the hook script's `-z "$RESULT"` check passes and it gets wrapped in `<system-reminder>` tags and injected — polluting the context with "no results" noise.

Fix: grep for "No matching topics found" and return empty context when detected.

### Debugging Tools

```bash
# Check hook health
hermes hooks doctor

# Test with synthetic payload (note: uses different payload format than actual runtime)
hermes hooks test pre_llm_call --payload-file /dev/stdin <<'EOF'
{"hook_event_name":"pre_llm_call","tool_name":null,"tool_input":null,"session_id":"test","cwd":"/home/chong","extra":{"user_message":"test query","is_first_turn":true}}
EOF

# Test directly (matches actual runtime format)
echo '<actual payload json>' | ~/.hermes/scripts/recall_hook.sh
```

### Key Log Entries

```
# Hook skipped (not allowlisted)
WARNING agent.shell_hooks: shell hook for pre_llm_call (~/.hermes/scripts/recall_hook.sh) not allowlisted — skipped

# Hook registered (auto-approved)
INFO agent.shell_hooks: shell hook auto-approved via --accept-hooks / env / config: pre_llm_call -> ~/.hermes/scripts/recall_hook.sh
INFO agent.shell_hooks: shell hook registered: pre_llm_call -> ~/.hermes/scripts/recall_hook.sh (matcher=None, timeout=30s)
```

**No log on successful execution** — only errors/timeouts produce logs. This makes "is it running?" hard to answer from logs alone. Use `hermes hooks test` instead.

### Architecture Notes

- Shell hooks register on the **same** `PluginManager._hooks` dict as Python plugins (singleton via `get_plugin_manager()`)
- Gateway startup calls `register_from_config()` at `gateway/run.py:3104`
- Hook callback is a closure from `_make_callback()` that calls `_spawn()` (subprocess)
- Plugin manager is module-level singleton (`hermes_cli/plugins.py:1177-1184`)
- `run_agent.py:11080` calls `invoke_hook("pre_llm_call", ...)` every turn
