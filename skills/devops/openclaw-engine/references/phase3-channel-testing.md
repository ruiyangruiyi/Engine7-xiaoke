# Phase 3 Channel Layer — Testing Notes (2026-05-27)

## Test Bot
- **Bot**: TestEngine#4251
- **ID**: 1509036814885978115
- **Server**: 1110873027861819392

## Configuration
```json
{
  "channels": {
    "discord": {
      "token": "<test-bot-token>",
      "guild": { "requireMention": true },
      "dm": { "pairing": true },
      "allowBots": true
    }
  }
}
```

## Issues Found During Testing

### 1. MESSAGE CONTENT INTENT not enabled
- **Symptom**: `messageCreate` event never fires (0 logs after 10s)
- **Cause**: Discord Developer Portal → Bot → Privileged Gateway Intents → MESSAGE CONTENT INTENT was off
- **Fix**: Enable all 3 privileged intents (PRESENCE, SERVER MEMBERS, MESSAGE CONTENT)
- **Must restart engine after enabling**

### 2. DM messages not received
- **Symptom**: Guild messages work ✅ but DM doesn't arrive
- **Cause**: discord.js requires `partials: [Partials.Channel, Partials.Message]` for uncached DM channels
- **Note**: discord.py doesn't need this — discord.js specific

### 3. DM reply target confusion
- **Symptom**: DM reply fails because target is DM channel ID, not user ID
- **Fix**: `send()` now tries `channels.fetch(target)` first (works for DM channels), then falls back to user ID

## Test Flow
1. `@TestEngine 你好` in guild → expect reply ✅ (after Intent fix)
2. DM TestEngine directly → expect reply ✅ (after Partials fix)
3. `msg_send` tool call via LLM → expect message delivered via ChannelManager ✅

## Key Lesson
> discord.js bot setup: Intents (code) + Privileged Gateway Intents (portal) + Partials (code) are THREE separate requirements. Missing any one silently breaks message reception.
