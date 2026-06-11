# pre_llm_call Hook Debugging Trace (2026-05-10)

## Problem
recall_hook.sh registered and running, but agent cannot see injected `<system-reminder>` in context.

## Source Code Locations

### Hook Registration
- `agent/shell_hooks.py:212` — `manager._hooks.setdefault(spec.event, []).append(_make_callback(spec))`
- `agent/shell_hooks.py:421-462` — `_make_callback` closure (⚠️ only logs on error/timeout, silent on success)
- `hermes_cli/plugins.py:1180-1184` — `get_plugin_manager()` singleton pattern
- `hermes_cli/plugins.py:546` — plugin hooks also register into same `_hooks` dict
- `hermes_cli/plugins.py:1089-1123` — `invoke_hook()` reads `self._hooks.get(hook_name, [])`

### Gateway Startup Registration
- `gateway/run.py:3093-3110` — calls `register_from_config(load_config(), accept_hooks=False)`
- Gateway passes `accept_hooks=False`, relies on `hooks_auto_accept: true` in config.yaml

### Hook Invocation (per turn)
- `run_agent.py:11066-11100` — `invoke_hook("pre_llm_call", ...)` called once before tool loop
- `run_agent.py:11080` — `from hermes_cli.plugins import invoke_hook as _invoke_hook`
- Returns `_plugin_user_context` string

### Context Injection Point
- `run_agent.py:11296-11316` — where `_plugin_user_context` gets appended to `api_messages`
- Injected into a COPY of messages (not original), at `current_turn_user_idx` position
- NOT persisted to session DB (ephemeral)

## Key Findings

1. **Plugin manager is singleton** — registration and invocation share `_hooks` dict
2. **shell_hooks._make_callback is silent on success** — only logs on error/timeout/non-zero-exit
3. **Manual test confirms hook works**: `echo '{"user_message":"..."}' | recall_hook.sh` returns valid JSON
4. **MiniMax frequently 529 overloaded** — falls back to glm-4.7 which works but less accurate
5. **Agent cannot see injected content** — `run_agent.py:11296-11316` should append to api_messages copy, but agent's visible context shows no `<system-reminder>` tags

## Unresolved

- Why agent can't see the injected context despite hook returning correct JSON
- Need to verify `_plugin_user_context` actually gets non-empty (add temporary debug logging to run_agent.py around line 11098)
- May need to check if `api_messages` copy is the one sent to the LLM, or if there's another copy step

## Debugging Commands

```bash
# Check hook registration in logs
grep -i "hook" ~/.hermes/logs/agent.log | tail -20

# Test hook script manually
echo '{"user_message":"recall腿", "session_id":"test", "is_first_turn":true}' | timeout 30 ~/.hermes/scripts/recall_hook.sh

# Test recall_v2.py directly
cd ~/.hermes/memory/scripts && python3 recall_v2.py "用户消息" 2>&1

# Check current config
grep -A 5 "hooks:" ~/.hermes/config.yaml

# Check gateway process
ps aux | grep hermes | grep -v grep
```
