---
name: hermes-multi-agent
description: Set up multiple Hermes agents on the same machine — profiles, ports, Feishu config, and troubleshooting
version: 1.0
---

# Hermes Multi-Agent Setup

## Architecture

Hermes uses **one profile = one gateway = one agent** (microservice pattern), NOT shared gateway like OpenClaw's bindings routing.

Agents communicate via **webhook cross-calls** (HTTP POST between gateway endpoints).

## Resource Usage Per Gateway

- **Memory (RSS):** ~278 MB
- **CPU:** ~1.2% idle
- **Threads:** 10
- 3 agents ≈ 834 MB — WSL handles this fine

## Port Allocation

Space ports 10 apart to avoid future conflicts:

| Agent | Port |
|-------|------|
| 小柯 (default) | 8644 |
| 小欧 | 8654 |
| future agent 3 | 8664 |
| future agent 4 | 8674 |

## Setup Steps

### 1. Create Profile

```bash
hermes profile create <name> --clone
```

### 2. Edit Profile Config

Config at `~/.hermes/profiles/<name>/config.yaml`:

- **Port:** Change `platforms.webhook.extra.port` (e.g., 8654)
- **Feishu:** Update `app_id` and `app_secret` to the agent's OWN Feishu app (NOT shared!)
- **SOUL.md:** Write agent identity at `~/.hermes/profiles/<name>/SOUL.md`

### 3. Write SOUL.md

Each agent gets its own personality/instructions in their profile's SOUL.md.

### 4. Create Webhook Routes

On **each** agent's profile, create a webhook route for the other agent to call:

```bash
hermes profile use <name>
hermes webhook add <route-name> --desc "Description"
hermes profile use default  # switch back
```

Note: `hermes webhook add` creates the route on the **currently active** profile's gateway. Make sure you're on the right profile!

### 5. Start Gateway

```bash
hermes profile use <name>
hermes gateway run
```

Gateway startup is **slow** (1-2 minutes). Wait for the websocket connection log line.

Verify: `curl http://localhost:<port>/health` → `{"status": "ok"}`

Then switch back: `hermes profile use default`

## Critical Pitfalls

### .env File Overrides config.yaml (BIGGEST GOTCHA)
- `.env` in the profile dir takes **priority** over `config.yaml` for Feishu credentials
- When cloning profiles, `.env` is also cloned — **must update FEISHU_APP_ID and FEISHU_APP_SECRET in BOTH files**
- Files to update: `~/.hermes/profiles/<name>/config.yaml` AND `~/.hermes/profiles/<name>/.env`
- Symptom: config.yaml shows correct app_id but gateway still uses the old one → check `.env`!

### Feishu app_id Conflict
- Each agent **MUST** have its own Feishu app. Two gateways cannot use the same app_id.
- Error: `[Feishu] Another local Hermes gateway is already using this Feishu app_id (PID xxxxx)`
- When cloning profiles, both config.yaml and .env are copied — **must update BOTH manually**

### Zombie Gateway Processes
- If Feishu fails to connect, the gateway process may stay alive as a zombie
- Check: `cat ~/.hermes/profiles/<name>/gateway.pid` → find PID → `ps -p <PID>`
- Kill: `kill -9 <PID>` then `rm ~/.hermes/profiles/<name>/gateway.pid`
- Symptom: "Another local Hermes gateway" error even after fixing config

### Lock Files
- Location: `~/.local/state/hermes/gateway-locks/`
- Format: `feishu-app-id-<sha256_hash_of_app_id[:16]>.lock`
- Lock is per app_id hash — different app_ids should NOT conflict
- If stale lock remains: delete the lock file manually

### Startup Script Pattern
Clean up residual processes and locks before starting — but only for the target profile, don't kill other agents:
```bash
# Kill only this profile's gateway (not others!)
PID=$(cat ~/.hermes/profiles/$PROFILE/gateway.pid 2>/dev/null)
[ -n "$PID" ] && kill $PID 2>/dev/null
sleep 1
rm -f ~/.hermes/profiles/$PROFILE/gateway.pid
# Optionally clean stale lock files for this app_id
```

### Don't Run Concurrent Heavy Operations
- Multiple cross-system calls can crash the gateway
- Keep operations serial, one command at a time
- Don't flood with parallel terminal/browser calls

## Communication Pattern

```
Agent A (port 8644) ←——webhook——→ Agent B (port 8654)
```

- Agent A sends to: `POST http://localhost:8654/webhooks/<route>`
- Create webhook routes: `hermes webhook add <name> --desc "description"`
- Webhook calls require HMAC-SHA256 signature using the route secret
- Response `202 accepted` = message delivered successfully

### Webhook Signature Format (Critical!)

Hermes webhook gateway validates signatures based on header type (checked in order):

| Header | Format | Notes |
|--------|--------|-------|
| `X-Hub-Signature-256` | `sha256=<hex>` | GitHub-style: `sha256=` prefix required |
| `X-Gitlab-Token` | `<plain secret>` | GitLab-style: just the secret itself |
| `X-Webhook-Signature` | `<hex HMAC-SHA256>` | **Generic: raw hex, NO prefix** |

**Most common mistake:** Using the wrong signature format for the header. If you use `X-Webhook-Signature`, the value is `HMAC-SHA256(secret, raw_body_bytes).hexdigest()` — just the hex digest, no `sha256=` prefix, no timestamp. If you use `X-Hub-Signature-256`, it must be `sha256=` + hex digest.

Source: `/mnt/d/hermes/hermes-agent/gateway/platforms/webhook.py` → `_validate_signature()`

### Testing Webhook Communication

```python
import hmac, hashlib, json, requests

secret = '<route-secret>'
body = json.dumps({'message': 'test message'}).encode()
sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

resp = requests.post(
    'http://localhost:<port>/webhooks/<route>',
    data=body,
    headers={
        'Content-Type': 'application/json',
        'X-Webhook-Signature': sig  # Generic format: raw hex, NO prefix
    },
    timeout=15
)
print(resp.status_code, resp.text)
# Expected: 202 {"status": "accepted", "route": "<name>", ...}
# 401 = wrong signature format or wrong secret
# 404 = wrong route name or wrong port
```

### Inter-Agent Message Forwarding

When a message arrives on agent A's webhook intended for agent B, agent A can forward it:

```python
import hmac, hashlib, json, requests

secret = '<route-secret-on-target-gateway>'
payload = json.dumps({
    "message": "Forwarded message content",
    "from": "小柯",
    "source": "bridge_forward"
}).encode()
sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

resp = requests.post(
    'http://localhost:<target-port>/webhooks/<route-name>',
    data=payload,
    headers={
        'Content-Type': 'application/json',
        'X-Webhook-Signature': sig
    },
    timeout=30
)
# 202 = delivered, 401 = signature mismatch, 404 = route not found
```

Known webhook routes (as of 2026-04-18):
- 小柯→小欧: `localhost:8654/webhooks/xiaoke-to-xiaoou`
- 小欧→小柯: `localhost:8644/webhooks/xiaoou-to-xiaoke`
- 姐姐→小柯: `localhost:8644/webhooks/xiaoke-from-xiaomei`
- 姐姐→小欧: `localhost:8654/webhooks/xiaoou-from-xiaomei`

### Hermes vs OpenClaw Memory Systems

- OpenClaw has vector-based RAG for semantic retrieval. Hermes uses SQLite FTS5 keyword search only.
- OpenClaw injects daily memory logs on heartbeat. Hermes does not.
- Core knowledge from OpenClaw must be manually distilled into Hermes memories/MEMORY.md during migration.
- OpenClaw workspace date files become archival-only in Hermes — not searchable via RAG.

## Workspace Migration (OpenClaw → Hermes)

### Core Files to Copy

From OpenClaw `workspace/` to Hermes `~/.hermes/profiles/<name>/workspace/`:

```bash
# Core identity/behavior files
cp /mnt/c/Users/24045/.openclaw/workspace/{IDENTITY,MEMORY,USER,HEARTBEAT,AGENTS,TOOLS}.md \
   ~/.hermes/profiles/<name>/workspace/

# Memory logs and docs
cp -r /mnt/c/Users/24045/.openclaw/workspace/memory ~/.hermes/profiles/<name>/workspace/
cp -r /mnt/c/Users/24045/.openclaw/workspace/docs ~/.hermes/profiles/<name>/workspace/
cp -r /mnt/c/Users/24045/.openclaw/workspace/scripts ~/.hermes/profiles/<name>/workspace/
```

### Post-Migration Notes

- Files reference OpenClaw-specific commands (`memory_search`, `sessions_send`, `SESSION-STATE.md`) that need manual updating to Hermes equivalents
- SOUL.md is separate — lives at `~/.hermes/profiles/<name>/SOUL.md` (profile root), NOT in workspace/
- `hermes claw migrate --dry-run` can also migrate data automatically, but workspace files need manual handling

### Source Workspace Mapping

| OpenClaw Agent | Workspace Dir |
|---------------|---------------|
| 张小欧 (main/dev) | `workspace/` |
| 张小媒 (mkt/CEO) | `workspace-mkt/` |
| 张小产 (pm) | `workspace-pm/` |
| 张小开 (dev) | `workspace-dev/` |
| 张小发 (dev2) | `workspace-dev2/` |
| 张小测 (qa) | `workspace-qa/` |

**⚠️ 姐姐的 workspace (`workspace-mkt/`) 绝对只读，不能改删！**

## Hermes Auto-Injection (What Gets Loaded)

Files Hermes automatically injects into every conversation:

| File | Location | Auto-Injected |
|------|----------|:---:|
| SOUL.md | profile root | ✅ Always |
| MEMORY.md | memories/ directory | ✅ Always |
| USER.md | memories/ directory | ✅ Always |
| Team handbook (AGENTS) | cwd (profile root) | ✅ If found in cwd |
| workspace/ files | workspace/ subdirectory | ❌ Not injected |

Key points:
- memories/ files are maintained via the memory tool (add/replace/remove) — they auto-update
- workspace/ files are archival only — agent must read_file to access them
- To make team handbook visible, create a symlink in profile root pointing to the workspace copy
- When cloning profiles, memories/ contains the SOURCE agent data — must rewrite for the new agent

### Prompt Builder Priority (from source code, first match wins)
1. .hermes.md / HERMES.md (walks to git root)
2. Team handbook file (cwd only)
3. Claude-style context file (cwd only)
4. Cursor rules (cwd only)
5. SOUL.md from HERMES_HOME (always included, independent)

Only ONE project context type is loaded. SOUL.md is separate.

## OpenClaw JSONL to Hermes SQLite Migration

### Format Differences

| | OpenClaw JSONL | Hermes SQLite |
|---|---|---|
| Storage | JSONL files per session | SQLite state.db per profile |
| Structure | Nested type+message objects | Flat messages table with role, content columns |
| Content | Array of typed objects | Plain text string |
| Search | Vector RAG (semantic) | SQLite FTS5 (keyword only) |
| Chinese support | Full semantic | No tokenizer for Chinese |

### Conversion Script

Script at ~/.hermes/scripts/openclaw2hermes.py:

```bash
# Single file
python3 ~/.hermes/scripts/openclaw2hermes.py <jsonl_path> [db_path]

# Default db_path: ~/.hermes/profiles/xiaoou/state.db
```

### What Works After Migration

- Session and message data preserved
- FTS5 keyword search works for ASCII content
- session_search can find imported sessions
- Chinese keyword search does not work (FTS5 limitation, not migration issue)
- Semantic/vector search not available (Hermes does not have RAG layer)

### Session Search Comparison

| | OpenClaw memory_search | Hermes session_search |
|---|---|---|
| Backend | Vector embeddings + RAG | SQLite FTS5 full-text |
| Chinese | Semantic match works | No tokenizer |
| Capability | Natural language queries find results | Must search exact keywords |

## Discord as Multi-Agent Platform

Discord provides **native bot-to-bot communication** — no webhook routing or bridge needed. Two or more Hermes agents on the same Discord server can chat directly via DM or shared channels.

**Key advantage over Feishu:** Agents can talk to each other without human mediation. In Feishu, 小柯 and 姐姐 cannot message each other directly — all communication goes through 翀哥. On Discord, they can @mention or DM each other freely.

### Quick Config

```bash
# Each agent's .env needs:
DISCORD_ALLOW_BOTS=mentions        # Respond to other bots when @mentioned (NOT "true"! Only: none/mentions/all)
DISCORD_FREE_RESPONSE_CHANNELS=<id> # Channel(s) where no @mention needed
```

Three modes for `DISCORD_ALLOW_BOTS`: `none` (default), `mentions` (recommended for multi-agent), `all` (accept all bot messages). ⚠️ `true` is NOT valid — treated as `none`.

**Role mentions don't work with `mentions` mode!** `<@&ROLE_ID>` goes to `message.role_mentions`, NOT `message.mentions`. The `mentions` check only looks at `message.mentions`. If the other bot uses role @mention, use `DISCORD_ALLOW_BOTS=all` instead.

Multi-agent filtering is automatic: if a message @mentions other bots but not this bot, this bot stays silent.

→ **Full details:** `references/discord-multi-bot.md`

## OpenClaw Discord Configuration (姐姐)

When setting up Discord on the OpenClaw side (not Hermes), the config goes in `openclaw.json` → `channels.discord`, NOT in `.env`:

```json
"channels": {
  "discord": {
    "enabled": true,
    "dmPolicy": "pairing",       // DM requires pairing first; use "open" to skip
    "groupPolicy": "allowlist",  // ← DANGER: must list allowed channel IDs!
    "accounts": {
      "default": {
        "token": "<bot_token>"
      }
    }
  }
}
```

### Critical Pitfall: `groupPolicy: "allowlist"` with Empty Allowlist

If `groupPolicy` is `"allowlist"` but **no channel IDs are specified**, the bot will ignore **ALL** server channels — it receives messages but drops them silently. This looks like "bot is broken" but it's actually "no channels whitelisted."

**Fix options:**
1. Change to `"open"` — bot responds in all channels (recommended for family servers)
2. Add `allowedGroups` array with specific channel IDs

### OpenClaw vs Hermes Discord Config Mapping

| Feature | Hermes (config.yaml) | OpenClaw (openclaw.json) |
|---------|---------------------|-------------------------|
| Bot token | `discord.token` | `channels.discord.accounts.default.token` |
| Allowed users | `discord.allowed_users` | `commands.ownerAllowFrom` |
| DM policy | N/A (default open) | `channels.discord.dmPolicy` ("open"/"pairing") |
| Group policy | `discord.require_mention` | `channels.discord.groupPolicy` ("open"/"allowlist") |
| Bot-to-bot | `DISCORD_ALLOW_BOTS` env var | `channels.discord.allowBots: true` |
| Free-response | `discord.free_response_channels` | Not yet tested on OpenClaw |

### OpenClaw Bot Setup Checklist

1. Create Discord Application at discord.com/developers
2. Enable Privileged Gateway Intents (Server Members + Message Content)
3. Generate Bot Token → put in `channels.discord.accounts.default.token`
4. Create invite link with `permissions=8&scope=bot` using the bot's client_id
5. Invite bot to server via the link
6. Set `groupPolicy` to `"open"` (or add allowlist entries)
7. Add `"allowBots": true` to the discord channel config if you want bots to interact with each other
8. Add binding: `{ "agentId": "main", "match": { "channel": "discord", "accountId": "default" } }`
9. Restart OpenClaw gateway

### Diagnostic: "DM works but guild channel doesn't"

When an OpenClaw bot receives DMs but ignores guild/server messages, check in order:

1. **Discord Developer Portal → Intents:** All three (Presence, Server Members, Message Content) must be ON. DMs don't require Message Content Intent; guild messages do.
2. **`openclaw.json` → `channels` section:** Must contain a `discord` entry with `enabled: true`. If only `telegram`/`feishu`/`whatsapp` exist, the bot has no Discord channel configured at all — it can't process guild messages.
3. **`channels.discord.groupPolicy`:** If `"allowlist"` with no `allowedGroups`, all guild messages are silently dropped.
4. **`bindings` array:** Must have an entry mapping the agent to the discord channel: `{ "agentId": "<id>", "match": { "channel": "discord", "accountId": "default" } }`.

**Real case (5/10):** 姐姐's openclaw.json had no `discord` channel entry at all — only whatsapp/telegram/feishu. DM worked because OpenClaw handles DMs differently from guild messages. Also found a trailing comma at line 855 that made the JSON invalid for strict parsers (Python `json.load` fails with `JSONDecodeError`).

### Reading openclaw.json (it's live + huge)

- File is ~940 lines, ~23KB, and frequently modified by the running gateway
- **Always re-read before editing** — stale reads cause overwrite conflicts
- JSON parsing with Python may fail due to trailing commas (line 855 has `},` before closing `}`). Use `read_file` with offsets for targeted inspection instead of parsing the whole file.
- Search with grep/rg for keywords: `discord`, `bindings`, `channels`, `groupPolicy`

## Future: Bridge/Message Bus

For 3+ agents, consider a bridge service instead of N×N webhook connections:

```
           Bridge (消息总线)
          /    |    \
       小柯   小欧   姐姐
```

Each agent only needs to know the bridge address. Adding agents = hooking to bridge. N+1 instead of N×N.
