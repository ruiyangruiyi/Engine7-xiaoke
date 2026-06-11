# Hermes Source Code Patches

Custom patches applied to `/mnt/d/hermes/hermes-agent/` (upstream: `NousResearch/hermes-agent`).

## Patch Index

### 001 - Discord Reply Mute Bots

**Date:** 2026-05-26
**Commit:** `fb1294df0`
**File:** `gateway/platforms/discord.py` L1392-1410 (in `send()` method)

**What:** When replying to a Discord message, check if the message author is in `DISCORD_REPLY_MUTE_BOTS` env var. If yes, skip the reply reference so the muted bot gets no notification.

**Why:** Prevent 小柯↔CC Bot reply loops. 小柯 auto-replies to messages in shared Discord channels; CC Bot would see the reply reference notification and potentially respond, creating an infinite loop. By muting the reference, CC doesn't know 小柯 replied.

**Env var:**
```bash
# ~/.hermes/.env
DISCORD_REPLY_MUTE_BOTS=1504373837880627280  # CC Bot, comma-separated for multiple
```

**Patch location:** `~/.hermes/patches/discord-reply-mute-bots/001-discord-reply-mute-bots.patch`

**Apply after pull:**
```bash
cd /mnt/d/hermes/hermes-agent
git apply ~/.hermes/patches/discord-reply-mute-bots/001-discord-reply-mute-bots.patch
```

**Implementation details:**
- The `send()` method already does `await channel.fetch_message(int(reply_to))` to build the reply reference
- Added a check: read `DISCORD_REPLY_MUTE_BOTS`, split by comma, check if `ref_msg.author.id` is in the set
- If matched: set `ref_msg = None` → `reference = None` → message sent without reply reference
- The message text is sent normally (still visible in the channel), just no "replying to" link
- To actively talk to CC: use `@CC` in the CC channel (`1504385800366854234`) — not affected by this patch

**姐姐's equivalent:** 姐姐 (OpenClaw) strips CC's ID from Discord replies at the plugin level. Same effect, different mechanism.

## Re-applying All Patches After Upgrade

```bash
cd /mnt/d/hermes/hermes-agent
git pull  # may overwrite patched files
for patch in ~/.hermes/patches/*/0*.patch; do
    git apply "$patch" || echo "FAILED: $patch"
done
```
