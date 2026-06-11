# Discord Multi-Bot Communication

Hermes Discord adapter has native support for bot-to-bot conversation — no webhook routing needed. Two or more Hermes agents on the same Discord server can chat directly with each other in channels or DMs.

## Key Environment Variables

### `DISCORD_ALLOW_BOTS`
Controls how the bot handles messages from **other Discord bots** (default: `"none"`):

| Value | Behavior |
|-------|----------|
| `"none"` | Ignore all bot messages (default, safe) |
| `"mentions"` | Only respond when another bot **@mentions** this bot |
| `"all"` | Respond to ALL bot messages (noisy, use with caution) |

**Recommended for multi-agent:** Use `"mentions"` — agents only talk when explicitly addressed.

### `DISCORD_FREE_RESPONSE_CHANNELS`
Comma-separated channel IDs where the bot responds **without requiring @mention**. Creates a free-chat room feel.

Config via env var or `config.yaml`:
```yaml
discord:
  free_response_channels: "1234567890,9876543210"
  # or as YAML list:
  # free_response_channels:
  #   - 1234567890
  #   - 9876543210
```

Free-response channels also **skip auto-threading** — bot replies inline instead of creating a new thread.

### `DISCORD_REQUIRE_MENTION`
Default `"true"`. In normal (non-free-response) channels, bot only responds when @mentioned. Set `"false"` to respond to everything (dangerous).

## Multi-Agent Filtering Logic (Source: discord.py ~L740-790)

When multiple bots share a channel, Hermes has smart filtering:

1. **If message @mentions other bots but NOT this bot** → this bot stays silent
2. **If message @mentions this bot** → this bot responds
3. **If message @mentions no bots** (general chat) → falls through to `DISCORD_REQUIRE_MENTION` / free-response logic
4. **DMs** → always responded to (no mention filtering in DMs)

This prevents the "all bots answering the same message" problem.

## Setup Pattern for Two Agents

```
# 小柯's .env
DISCORD_BOT_TOKEN=<xiaoke_bot_token>
DISCORD_ALLOWED_USERS=[<chong_user_id>]  # Only needed for human auth
DISCORD_ALLOW_BOTS=mentions
DISCORD_FREE_RESPONSE_CHANNELS=<family_channel_id>

# 姐姐's .env (when migrated to Hermes)
DISCORD_BOT_TOKEN=<xiaomei_bot_token>
DISCORD_ALLOWED_USERS=[<chong_user_id>]
DISCORD_ALLOW_BOTS=mentions
DISCORD_FREE_RESPONSE_CHANNELS=<family_channel_id>
```

Then 姐姐 can DM 小柯 directly, or @小柯 in a shared channel — no human mediation needed.

## Channel Topology Options

### 1. Private DM (1-on-1)
Bots can DM each other directly. No channel setup needed. Just needs `DISCORD_ALLOW_BOTS` set.

### 2. Family Channel (free-response)
Create a channel like `#family-chat`, set as free-response on both bots. All three (human + 2 bots) can chat freely without @mentions.

### 3. General Channel (mention-based)
Normal channels where bots only respond when @mentioned. Good for shared servers with other users.

## Bot Permissions Required

When creating the Discord bot in Developer Portal, enable these **Privileged Gateway Intents**:
- ✅ Server Members Intent
- ✅ Message Content Intent

Permissions integer: `274878286912`

## OpenClaw (姐姐) Bot-to-Bot Config

OpenClaw Discord plugin supports `allowBots` at the channel level:

```json
"channels": {
  "discord": {
    "enabled": true,
    "allowBots": true,
    "dmPolicy": "open",
    "groupPolicy": "open",
    "accounts": {
      "default": {
        "token": "<bot_token>"
      }
    }
  }
}
```

Without `allowBots: true`, the OpenClaw bot will **ignore all messages from other Discord bots**, even if @mentioned. This is the OpenClaw equivalent of Hermes's `DISCORD_ALLOW_BOTS=mentions`.

**Real case (5/11):** 姐姐 could not see 小柯's messages in the shared Discord channel until `allowBots: true` was added to `openclaw.json` → `channels.discord`.

## Hermes Discord "DM works but guild doesn't" Debugging (Real Case 5/12)

When a Hermes Discord bot receives DMs but ignores guild/server channel messages, check in this order:

### 1. Discord Developer Portal → Privileged Gateway Intents
All three must be ON:
- ✅ Presence Intent
- ✅ Server Members Intent
- ✅ **Message Content Intent** (DMs work without this; guild messages do NOT)

### 2. Hermes Code Intents (should already be set)
Source `discord.py` L631-634:
```python
intents.message_content = True    # Required for reading message text
intents.guild_messages = True     # Required for receiving guild events
intents.dm_messages = True        # Required for DM events
```
These are hardcoded ON — only the Developer Portal toggle can disable them.

### 3. `default_group_policy` in config.yaml
Must be `open` (not `allowlist` with empty allowlist). Check:
```bash
grep default_group_policy ~/.hermes/config.yaml
```

### 4. Thread Cache Loss After Gateway Restart (KEY FINDING)
Hermes uses `self._threads` dict to track threads it has participated in. After a gateway restart, this cache is **empty**. In `_handle_message` (L4038+):
- DMs always pass through
- Guild channels check `require_mention` → then check `in_bot_thread`
- If the bot previously responded in a thread, after restart it won't recognize that thread → `in_bot_thread=False`
- The bot still gets the raw Discord event, but `_handle_message` may filter it at the mention/allowed-channels layer

**Symptom:** Bot worked in a guild channel before restart, then stopped.
**Fix:** Send a fresh @mention to the bot in the channel (not in an old thread) to re-establish the session.

### 5. Role Mention vs User Mention (Subtle!)
`<@&ROLE_ID>` (role mention) does NOT appear in `message.mentions`. Only `<@USER_ID>` does. If the user @mentions a role that includes the bot, the bot won't detect itself as mentioned → the `DISCORD_IGNORE_NO_MENTION` filter (default `true`) drops the message.

**Fix:** Always @mention the bot user directly, not via role.

### 6. `DISCORD_IGNORE_NO_MENTION` Default
Env var defaults to `"true"` (L761-780). When true, in guild channels:
- If humans are mentioned but not this bot → message dropped
- If no bots are mentioned and channel not in free_response → message dropped
- Only passes through if bot is directly in `message.mentions`

### 7. Discord Connection Stability (WSL-specific)
Discord gateway may RESUME every 2 minutes due to WSL2 network issues. This doesn't break DMs but can cause guild event caching issues. Check:
```bash
grep "RESUMED\|reconnect" ~/.hermes/logs/agent.log | tail -20
```

### Diagnostic Commands
```bash
# Check which channel IDs the bot has seen
grep -oP 'chat=\K[0-9]+' ~/.hermes/logs/gateway.log | sort -u

# Check for guild messages (vs DM-only)
grep "guild=" ~/.hermes/logs/gateway.log | grep -v "guild=None" | tail -10

# If empty = bot never received a guild message (intent or permission issue)

# Monitor live for new messages
wc -l ~/.hermes/logs/gateway.log  # baseline
# ... user sends @mention in guild channel ...
wc -l ~/.hermes/logs/gateway.log  # check if line count changed

# Check if bot sees any guilds at all
grep "channel.*directory\|guilds\|Connected as" ~/.hermes/logs/gateway.log | tail -5
```

### Config Comparison: OpenClaw guilds vs Hermes channels

| Feature | OpenClaw | Hermes |
|---------|----------|--------|
| Server whitelist | `guilds: { "server_id": { requireMention: false } }` | Not supported — use `free_response_channels` per channel |
| Group policy | `groupPolicy: "open"/"allowlist"` | `default_group_policy: open` + `allowed_channels` whitelist |
| Bot-to-bot | `allowBots: true` | `DISCORD_ALLOW_BOTS=mentions` |
| Free response | N/A | `free_response_channels: "ch_id1,ch_id2"` or `DISCORD_FREE_RESPONSE_CHANNELS` |

OpenClaw's `guilds` config tells the bot "respond in this server". Hermes has no server-level gate — it uses per-channel filtering. If `allowed_channels` is empty (default), all channels are accepted. The filtering is purely mention-based.

## Common Configuration Pitfalls (Real Cases 5/12)

### `allowed_users` Must Be a YAML List, NOT a Quoted String

When setting `allowed_users` programmatically via Python `yaml.dump`, passing a **string** `"[601, 702]"` produces a quoted YAML scalar that Hermes treats as a single string — not a list. The bot silently ignores ALL users.

**Wrong (Python passes a string):**
```yaml
allowed_users: '[601669300343799819, 1502999996616933428]'
```

**Correct (Python passes a list):**
```yaml
allowed_users:
  - 601669300343799819
  - 1502999996616933428
```

**Python fix:** Use `config['discord']['allowed_users'] = [601, 702]` (list object), NOT `config['discord']['allowed_users'] = '[601, 702]'` (string).

**Symptom:** Gateway log shows `WARNING gateway.run: Unauthorized user: <id> (<name>) on discord` for every message from that user. DMs work but guild messages are dropped.

### `free_response_channels` Overrides `require_mention`

If a channel ID is listed in `free_response_channels`, the bot responds in that channel **without requiring @mention**, regardless of `require_mention: true`. This is by design — free_response is an explicit opt-out of require_mention per channel.

**Gotcha:** Setting `require_mention: true` and wondering why the bot still responds without @mention in a channel? Check if that channel is in `free_response_channels`.

```bash
grep free_response_channels ~/.hermes/config.yaml
```

Source: `discord.py` L3531-3550 (`_discord_free_response_channels`).

### `DISCORD_ALLOW_BOTS` — Only Valid Values Are `none`, `mentions`, `all`

⚠️ **`true` is NOT a valid value!** The source code (`discord.py` L722-726) does exact string matching:

```python
allow_bots = os.getenv("DISCORD_ALLOW_BOTS", "none").lower().strip()
if allow_bots == "none":
    return  # reject
elif allow_bots == "mentions":
    if not self._client.user or self._client.user not in message.mentions:
        return  # reject unless @mentioned
# "all" falls through → accepted
```

There is NO `elif allow_bots == "true"` branch. Setting `DISCORD_ALLOW_BOTS=true` falls through without matching any condition → bot messages are silently dropped (same as `none`).

| Value | Behavior |
|-------|----------|
| `none` (default) | Ignore all bot messages |
| `mentions` | Only respond when @mentioned by a bot |
| `all` | Respond to all bot messages |
| ⚠️ `true` | **INVALID — treated as `none`!** |

**Real case (5/12):** Set `DISCORD_ALLOW_BOTS=true` thinking it was valid. Bot messages from 姐姐 were silently dropped with no error. Fixed by changing to `mentions`.

### Field Name Verification in Source Code

All `discord.*` config fields in `config.yaml` are read via `self.config.extra.get("field_name")` in `discord.py`. Key fields and their source code locations:

| config.yaml field | Source code line | Default |
|---|---|---|
| `require_mention` | L3524 | `true` (env: `DISCORD_REQUIRE_MENTION`) |
| `free_response_channels` | L3534 | empty |
| `allowed_users` | L4038+ (auth check) | empty (no restriction) |
| `allowed_channels` | L4038+ (channel filter) | empty (all allowed) |
| `token` | L648 | required |

All use **snake_case** (not camelCase). When in doubt, `grep -n "config.extra.get" discord.py`.

### Two-Layer Auth Check: `discord.py` → `gateway/run.py`

Bot messages go through **two separate auth layers**. Passing the first does NOT guarantee passing the second:

1. **Discord adapter (`discord.py` L714-730):** Checks `DISCORD_ALLOW_BOTS` — filters bot messages at the platform level. `all`/`mentions` lets bot messages through.

2. **Gateway core (`gateway/run.py` L4710-4718):** `_is_user_authorized()` checks if the user is in the allowlist. For bot users (`source.is_bot=True`), if `DISCORD_ALLOW_BOTS` is set to `mentions` or `all`, it returns `True` immediately (bypasses the human allowlist).

The `Unauthorized user` warning comes from layer 2. If you see it, the message passed Discord adapter filtering but was rejected at the gateway core.

**Real case (5/12):** `DISCORD_ALLOWED_USERS` in `.env` only had 翀哥's ID. 姐姐's bot messages passed Discord's `DISCORD_ALLOW_BOTS=all` check but were rejected by `_is_user_authorized()` because her ID wasn't in the allowlist. **Fix: Remove `DISCORD_ALLOWED_USERS` entirely** (no allowlist = accept all, same as 姐姐's OpenClaw config).

### `.env` Takes Priority Over `config.yaml` for Discord Auth

`DISCORD_ALLOWED_USERS` in `.env` is read by `gateway/run.py` `_is_user_authorized()` (L4658-4664). The `discord.allowed_users` field in `config.yaml` is read by `discord.py` `_is_allowed_user()` (L2164+). These are **two separate checks** that both must pass.

**Practical implication:** If you set `allowed_users` in `config.yaml` but NOT in `.env`, the gateway-level check (`_is_user_authorized`) will still deny users not in the env var. And vice versa. Simplest approach: **set it in ONE place only** (`.env` preferred since env vars are checked first in the auth chain), or remove both to accept all users.

**Real case (5/12):** Added 娘's ID to `config.yaml` `allowed_users` but `.env` `DISCORD_ALLOWED_USERS` still only had 爹's ID → messages still rejected. Removing `DISCORD_ALLOWED_USERS` from `.env` entirely solved it (no allowlist = accept all).

## Confirmed Working Config for Bot-to-Bot (5/12)

After extensive debugging, the following config works for 小柯 (Hermes) receiving messages from 娘 (OpenClaw bot) in a shared Discord server channel:

### 小柯's `.env` (Hermes side)
```
DISCORD_BOT_TOKEN=<token>
DISCORD_HOME_CHANNEL=<home_channel_id>
DISCORD_HOME_CHANNEL_THREAD_ID=
DISCORD_ALLOW_BOTS=all
# NO DISCORD_ALLOWED_USERS — removed to avoid blocking bot users at gateway layer
```

### 小柯's `config.yaml` (discord section)
```yaml
discord:
  auto_thread: false
  channel_prompts: {}
  free_response_channels: ''   # Empty = require_mention applies everywhere
  reactions: true
  require_mention: true
  token: <token>
  # NO allowed_users — removed
  # NO allowed_channels — removed
```

### Why `DISCORD_ALLOW_BOTS=mentions` Failed for Bot-to-Bot

With `DISCORD_ALLOW_BOTS=mentions`, the Discord adapter (`discord.py` L725-726) checks:
```python
if not self._client.user or self._client.user not in message.mentions:
    return  # reject
```

This relies on `message.mentions` containing the bot's user object. **But** there's a subtlety: the OpenClaw bot (姐姐) may format its mention differently than expected. If 姐姐 uses a **role mention** `<@&ROLE_ID>` instead of a **user mention** `<@USER_ID>`, Discord's API puts it in `message.role_mentions`, NOT `message.mentions`. The check fails silently.

**Practical fix:** Use `DISCORD_ALLOW_BOTS=all` if the other bot might use role mentions. Or ensure the other bot always uses direct user mentions `<@BOT_USER_ID>`.

### Debugging Flow for "Bot can't see other bot's messages"

1. Check gateway log for `Unauthorized user` warnings → gateway auth layer issue
2. Check gateway log for ANY line with the bot user ID → if absent, message never reached Hermes
3. If message reaches discord.py but not gateway core → check `DISCORD_ALLOW_BOTS` value (must be `none`/`mentions`/`all`, NOT `true`)
4. If message reaches gateway core but shows Unauthorized → check `DISCORD_ALLOWED_USERS` in `.env` (remove it entirely to accept all)
5. If message reaches bot but bot doesn't respond → check `require_mention` + `free_response_channels` + whether the mention is a role mention vs user mention
6. **Always check both layers:** `discord.py` adapter filtering AND `gateway/run.py` `_is_user_authorized()`

## Source Code References

- Bot message filtering: `gateway/platforms/discord.py` L714-730 (`DISCORD_ALLOW_BOTS`)
- Multi-agent mention filtering: L754-790 (smart bot-aware filtering)
- Free-response channels: L3531-3550 (`_discord_free_response_channels`)
- Guild message handling: L4038-4120 (`_handle_message` — allowed_channels, require_mention, thread cache)
- Intents setup: L624-640
- Official docs: `website/docs/user-guide/messaging/discord.md`
