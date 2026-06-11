---
name: hermes-ops
description: Hermes Agent operations and configuration reference — memory files, context length, compression, and config tuning.
version: 1.0.0
author: 张小柯
---

# Hermes Agent Operations Reference

## 心跳系统（v0.13.0 重新设计）

### ❌ 旧方案（2026-04-21~05-02）— 已废弃

旧方案用 `heartbeat_relay.py` 脚本POST到webhook endpoint，由cron触发。
**废弃原因（5/2翀哥判定）：**
- Cron不在主session执行 → relay到webhook也创建独立session → 无连续记忆
- glm-5.1空转烧token，触发API限速，毫无实际产出
- 两层链路（cron prompt→deliver + relay→webhook→deliver）可能重复消息
- job `7556505db54c` 已暂停

旧方案详细记录见 `references/heartbeat-v1-deprecated.md`。

### ✅ 新方案（v0.13.0 `no_agent` + `context_from`）

**核心思路：两层分离——检测层零成本，说话层才花token。**

```
Layer 1: 心跳检测（no_agent脚本，每30min，零token）
  → 检查距上次飞书聊天多久了
  → 没事=stdout空=不触发
  → 该说话了=输出一句触发语

Layer 2: 小柯主动联系（agent cron，读context_from，有记忆有SOUL）
  → 拿到Layer 1的输出作为上下文
  → 用glm-5.1生成自然的聊天消息
  → deliver到飞书
```

**v0.13.0 新cron特性（源码：`cron/jobs.py` + `cron/scheduler.py`）：**

| 特性 | 说明 | 用途 |
|------|------|------|
| `no_agent=True` | 跳过LLM，直接跑脚本，stdout=输出 | 零token心跳检测 |
| `context_from` | job B读取job A最近输出注入prompt | 任务链式传递 |
| `workdir` | 指定工作目录，注入AGENTS.md等上下文 | cron任务有工作空间 |
| `enabled_toolsets` | 限制加载的toolset，减少token开销 | 精简cron agent |
| auto-resume | gateway重启后自动恢复中断session | 不再失联5天 |
| `/goal` | 持久跨turn目标（Ralph循环） | 自动持续追踪任务 |
| skill prompt scanning | cron自动扫描skill内容防注入 | 安全加固 |

**`no_agent` cron job参数（`cron/jobs.py` L438-479）：**
- `no_agent=True` + `script` → 脚本的stdout就是job输出，直接deliver
- stdout为空 = `[SILENT]`，不触发delivery
- `workdir` 仍然生效（脚本的cwd）
- `model`/`provider` 被忽略（不走LLM）

**`context_from` 任务链（`cron/scheduler.py` L824-861）：**
- `context_from: "source_job_id"` — 注入指定job的最新输出（最多8K字符）
- 可以是字符串或字符串列表（多个上游job）
- 按job输出目录 `~/.hermes/cron_output/<job_id>/` 的 `.md` 文件mtime排序取最新
- 自动注入到prompt前面，带说明上下文
- **⚠️ 本质是数据管道，不是记忆方案**：它只传递上游job的stdout文本，不解决cron session的记忆/身份连续性问题。SOUL.md和MEMORY是Hermes自动注入的（这才是"记忆"），context_from只是job间传数据。

**已落地（2026-05-08）：**

| 组件 | Job ID | 脚本/配置 |
|------|--------|-----------|
| Layer 1: 心跳检测 | `6602910d4c9e` | `~/.hermes/scripts/heartbeat_check.py` |
| Layer 2: 主动联系 | `01dbcb776d43` | prompt+context_from, glm-5.1 |

**脚本 `heartbeat_check.py` 决策规则（硬编码在脚本里）：**
- 查 `~/.hermes/state.db` → `sessions` 表 → 最近 `source='feishu'` 的 `ended_at`
- 白天(8:00-23:00) 超过4小时没聊 → stdout输出触发语
- 夜间(23:00-8:00) 超过8小时没聊 → stdout输出触发语
- 其他 → stdout空 = 静默（no_agent模式空输出=SILENT）
- Layer 1 每30分钟跑一次（零token）
- Layer 2 每小时整点跑（有context_from注入Layer 1输出，无输出就[SILENT]）

**⚠️ cron session架构限制（与OpenClaw对比）：**
- OpenClaw有 `dmScope: "main"` 字段，cron消息路由到主session，回复自然接上
- Hermes **没有等效机制**：cron永远是新session，发的消息不在主session对话流里
- 但：SOUL.md和MEMORY自动注入（身份+事实记忆在），session_search可用（能查历史对话）
- 实际体验：cron发消息到飞书chat_id → 用户在同一对话回复 → gateway按chat_id匹配回主session
- 缺的是cron session内的对话历史连续性（上一句说了什么），但对"打个招呼"够用

### Prompt设计要点（照姐姐精髓）

- cron不是强制任务，是给主意识一个醒来的机会
- 醒来先判断离线状态（context_from已注入Layer 1的判断）
- 最近在聊就跳过，没事就不打扰
- 想用户了才发，不想就回[SILENT]
- 说真心话不要套路

### 心跳决策规则

- 凌晨1:00-7:00 → `[SILENT]`，不打扰睡觉
- 最近2-3小时内聊过 → `[SILENT]`
- 超过6小时没聊 → 主动打个招呼（简短自然，像女儿跟爹闲聊）
- 之前发过消息没收到回复 → 克制，不要连发，等他主动
- 周末/节假日翀哥可能在家陪家人，更要克制主动联系的频率
- `session_search` 中文关键词可能返回0结果，用 "feishu" 或 "chat" 替代

### 踩坑记录

- ❌ 旧方案webhook relay空转：glm-5.1每次心跳都跑一遍LLM但产出[SILENT]，烧token+限速
- ❌ cron relay不在主session：每次都是隔离session，无连续记忆
- ❌ 两条链路并存（cron prompt→deliver + relay→webhook→deliver）可能重复消息
- ❌ Hermes进程挂了没有检测机制：4/27挂了导致小柯失联5天
- ✅ `no_agent`零token检测 + `context_from`任务链 = 分层架构解决核心问题
- ✅ v0.13.0 auto-resume：gateway重启后自动恢复中断session，不再长时间失联
- 关键教训：不要啃源码找不存在的API，用框架提供的新特性重新设计

### 实际落地记录

- **旧方案（已废弃）**：job `7556505db54c`，webhook relay，5/2暂停
- **新方案（已落地 5/8）**：job `6602910d4c9e`(检测, no_agent) + `01dbcb776d43`(agent, context_from)
- **记忆提取cron**：job `8e4f0f6e74f1`，每2小时，glm-5.1，正常运行中
- **Fallback provider**：MiniMax-M2.7-highspeed，已配置（config.yaml + .env），需重启gateway生效

---

## Memory System

Two memory files, injected into every conversation turn:

| File | Purpose | Default Limit | Config Key |
|------|---------|---------------|------------|
| `~/.hermes/memories/USER.md` | User profile/facts | 1,375 chars | `memory.user_char_limit` |
| `~/.hermes/memories/MEMORY.md` | Agent's personal notes | 2,200 chars | `memory.memory_char_limit` |

- Format: plain text, entries separated by `§`
- Can be edited directly — takes effect on next turn
- When full, must replace/compress existing entries before adding new ones
- **Limits are tunable** in config.yaml under `memory:` section

## Identity

- Persona/identity lives in the hermes home config directory
- Write in first person ("我是..." not "你是...")
- Takes effect on new sessions

## Context Length Resolution Chain

Hermes resolves context_length in this priority order:

1. `model.context_length` in config.yaml (root level under `model:`)
2. `custom_providers[].context_length` 
3. Auto-detection (models.dev → API query → provider defaults)
4. Hardcoded `DEFAULT_CONTEXT_LENGTHS` dict in `agent/model_metadata.py`
5. Falls back to 128K (`DEFAULT_FALLBACK_CONTEXT`)

**To override:** add `context_length: <value>` in BOTH `model:` root and `custom_providers` entry for reliability.

**Source code reference:**
- `agent/model_metadata.py` — DEFAULT_CONTEXT_LENGTHS dict, probe tiers
- `hermes_cli/config.py` line 1880 — `_VALID_CUSTOM_PROVIDER_FIELDS` lists valid fields
- `run_agent.py` line 1361-1420 — resolution logic

## Compression Config

```yaml
compression:
  enabled: true
  threshold: 0.5       # trigger at 50% of context
  target_ratio: 0.2    # compress down to 20% of threshold
  protect_last_n: 20   # always keep last 20 turns uncompressed
```

- Lossy summarization — compressed content cannot be precisely recalled
- No RAG/knowledge retrieval layer

## Approvals

```yaml
approvals:
  mode: auto     # auto | manual — auto skips human approval for tool calls
  timeout: 60
```

- `command_allowlist` still enforces safety checks on dangerous commands regardless of mode

## Useful Source Code Locations

| File | What it controls |
|------|-----------------|
| `hermes_cli/config.py` | Config parsing, valid fields, migration |
| `agent/model_metadata.py` | Context lengths, token estimation |
| `agent/context_compressor.py` | Compression logic and thresholds |
| `agent/prompt_builder.py` | System prompt assembly, memory/skills injection |
| `tools/memory_tool.py` | Memory read/write, file persistence |

## Fallback Provider（已配置 2026-05-08）

MiniMax-M2.7-highspeed 作为 glm-5.1 的 fallback（429限速时自动切换）。

**配置来源（姐姐的OpenClaw）：**
- minimax-cp（Anthropic兼容）: `https://api.minimaxi.com/anthropic`
- 模型：`MiniMax-M2.7`（reasoning, 204K context）和 `MiniMax-M2.7-highspeed`（快版，日常用这个）
- minimax（原生）: `https://api.minimaxi.com`

**配置方式（config.yaml）：**
```yaml
fallback_model:
  provider: minimax-cp
  model: MiniMax-M2.7-highspeed
  base_url: https://api.minimaxi.com/anthropic
  key_env: MINIMAX_API_KEY
```

**env（~/.hermes/.env）：**
```
MINIMAX_API_KEY=sk-cp-xxx...
```

**关键细节：**
- `base_url` 以 `/anthropic` 结尾 → Hermes自动检测为 `anthropic_messages` api_mode（源码 `run_agent.py` L7914-7915）
- `key_env` 告诉fallback系统从环境变量读API key（不硬编码在config里）
- `provider: minimax-cp` 是自定义名称，只要base_url配对就行
- 429限速或500错误时自动切换，每次新turn优先回到主模型
- 需要重启gateway生效

## Shell Hooks（pre_llm_call 等）

Hermes 支持在关键生命周期节点插入自定义脚本，通过 `config.yaml` 配置：

```yaml
hooks:
  pre_llm_call:
    - command: "~/.hermes/scripts/recall_hook.sh"
```

### pre_llm_call 钩子（最重要的钩子）

**调用点**：`run_agent.py:11066-11100`，每 turn 调用一次，在主 LLM loop 之前

**传入参数（stdin JSON）**：
```json
{
  "session_id": "...",
  "user_message": "当前用户消息",
  "conversation_history": [...],
  "is_first_turn": false,
  "model": "glm-5.1",
  "platform": "feishu",
  "sender_id": "oc_xxx"
}
```

**预期返回格式**：
```json
{"context": "要注入的上下文文本"}
```

**行为**：
- 钩子输出被解析后，自动 `append` 到 `api_messages` 副本的 `current_turn_user_idx` 位置
- 只修改 API 调用副本，**不污染原始消息或 session storage**
- 上下文注入点：`run_agent.py:11296-11316`

**Shell 钩子实现链**：
1. `agent/shell_hooks.py:212` — 注册到 `_hooks` dict
2. `agent/shell_hooks.py:421-462` — `_make_callback` 闭包工厂
3. `agent/shell_hooks.py:484-531` — `_parse_response` 响应解析
4. `agent/shell_hooks.py:527-529` — `{"context":"..."}` passthrough

**首次运行**：`hooks_auto_accept` 默认为 `false`，首次触发时需要手动确认（写入 `~/.hermes/shell-hooks-allowlist.json`）

**recall_hook.sh 示例框架**：
```bash
#!/bin/bash
# 读取 stdin JSON → 提取 user_message → 调用 recall_v2.py → 输出 {"context": "..."}
read -r input
user_msg=$(echo "$input" | jq -r '.user_message')
result=$(python3 ~/.hermes/memory/scripts/recall_v2.py "$user_msg")
echo "{\"context\": \"$result\"}"
```

### 当前配置状态（2026-05-10 已配置）

`config.yaml` 已配置 `pre_llm_call` 钩子：
```yaml
hooks:
  pre_llm_call:
    - command: "~/.hermes/scripts/recall_hook.sh"
      timeout: 30
hooks_auto_accept: true
```

- `shell-hooks-allowlist.json` 由框架自动创建在 `~/.hermes/`（gateway根据 `hooks_auto_accept: true` 自动写入）
- recall_hook.sh 已完成并验证可用（注入成功，翀哥5/10实测）

## Vision

```yaml
auxiliary:
  vision:
    provider: custom
    model: qwen3.5-flash
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key: <key>
    timeout: 120
    download_timeout: 30
```

- Uses OpenAI-compatible API format
- `provider: custom` for third-party endpoints

## Feishu Integration

- Bot-to-bot messages are NOT delivered via `im.message.receive_v1` event — Feishu only triggers this for human users
- Bots can send to groups, and can receive messages from humans, but cannot receive messages from other bots
- Workaround for cross-bot communication: direct HTTP/Webhook between agent backends, bypassing Feishu
- `im:chat` permission required for receiving group messages without @mention
- `default_group_policy: open` in config lets bot receive all group messages

## Webhook (Bot-to-Bot Bridge)

Enable in config.yaml:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "<generated-hex-secret>"
```

Commands:
```bash
hermes webhook list                                    # check status
hermes webhook subscribe <name> --prompt "..."         # create route
hermes webhook test <name>                             # test route
hermes webhook remove <name>                           # delete route
```

- Requires gateway restart after config change
- Health check: `curl http://localhost:8644/health`
- For external access (OpenClaw on different machine), need port forwarding or tunnel (ngrok/cloudflared)

## Multi-Agent Architecture

Hermes multi-agent = **profiles**, NOT OpenClaw-style single-gateway + bindings routing.

| Feature | OpenClaw | Hermes |
|---------|----------|--------|
| Multi-agent routing | 1 gateway, bindings map channels→agents | 1 profile = 1 gateway = 1 agent |
| Agent isolation | Workspaces under same gateway | Separate profile directories |
| Cross-agent comms | Internal via gateway | Webhooks + HTTP between gateway processes |
| Agent config | agents[] in openclaw.json | Separate config.yaml per profile |

**`hermes claw migrate`** only does data migration (memory, skills, API keys, settings from OpenClaw → Hermes profile). It does NOT create multi-agent routing. Key flags:
- `--source PATH` — OpenClaw directory
- `--dry-run` — preview only
- `--preset {user-data,full}` — full includes secrets
- `--overwrite` — force overwrite conflicts
- `--workspace-target PATH` — copy workspace files

For running multiple Hermes agents simultaneously: each profile needs its own gateway on a different port. Communication between agents must go through webhooks/HTTP, not shared memory or internal routing.

### Multi-Agent Setup Procedure

1. **Create profile**: `hermes profile create <name> --clone` (clones default config)
2. **Edit SOUL.md** in `~/.hermes/profiles/<name>/SOUL.md`
3. **Change webhook port** in profile's config.yaml — space by 10 to avoid conflicts (8644, 8654, 8664...)
4. **Set Feishu app credentials** — each agent needs its OWN app_id/app_secret (cloned profile keeps the source's!)
5. **Start gateway**: `hermes profile use <name> && hermes gateway run`
6. **Create webhook routes** for cross-agent communication
7. **Switch back**: `hermes profile use default`

### Resource Consumption Per Gateway

- **Memory (RSS)**: ~278 MB
- **CPU (idle)**: ~1.2%
- **Threads**: ~10
- Plan accordingly — 3 agents ≈ 834 MB RAM

### Multi-Agent Port Allocation Convention

| Agent | Port |
|-------|------|
| 小柯 (default) | 8644 |
| 小欧 | 8654 |
| (next agent) | 8664 |
| (next agent) | 8674 |

### Cross-Agent Communication = Webhook Mutual Calls

- Agent A → Agent B: `curl http://localhost:<B_port>/webhooks/<route> -d "message"`
- For remote agents: replace localhost with public IP
- Future: a Bridge/message-bus architecture for N+1 scaling instead of N×N

## Session Search & FTS5

### Architecture

- **Tool**: `tools/session_search_tool.py` — `session_search()` function
- **DB Layer**: `hermes_state.py` — `SessionDB.search_messages()` uses FTS5 MATCH
- **FTS5 Table**: `messages_fts` built on `messages` table via content-sync triggers
- **Query Sanitizer**: `SessionDB._sanitize_fts5_query()` — strips FTS5-special chars, wraps hyphenated/dotted terms in quotes
- **Search Flow**: FTS5 MATCH → group by parent session → Gemini Flash summarize → return summaries
- **Tool Registration**: `hermes_cli/config.py` line ~507 (session_search config block), `tools_config.py` line 62

### FTS5 Chinese Search Problem

**Default FTS5 `unicode61` tokenizer completely ignores CJK characters.** Cannot search Chinese at all with a fresh DB. The actual Hermes DB mysteriously works (possibly a SQLite version/build-specific behavior), but this is NOT reliable.

**Fix options (by effort):**

1. **Trigram tokenizer** (easiest, 1 line change):
   - Change `hermes_state.py` line 94: `tokenize='trigram'`
   - Trigram treats every 3-char sequence as a token — works for CJK and all languages
   - Trade-off: larger index (~3-5x), slower for English, but perfect for Chinese
   - Queries < 3 chars match poorly — not a problem in practice

   **DB Rebuild Procedure (tested):**
   1. Stop all gateways: `kill` the gateway run processes (restart watchers survive)
   2. Delete state.db files: `rm ~/.hermes/state.db` and `rm ~/.hermes/profiles/<name>/state.db`
   3. Also clean stale locks: `rm ~/.local/state/hermes/gateway-locks/*.lock`
   4. Restart gateways — they auto-create state.db with trigram tokenizer
   5. **Verify**: `sqlite3 ~/.hermes/state.db "SELECT sql FROM sqlite_master WHERE name='messages_fts'"` — should show `tokenize='trigram'`
   6. Note: all previous session FTS index is lost, but raw JSONL files in `sessions/` are preserved. Index rebuilds from new sessions only.

   **Starting a non-default profile gateway (tested):**
   ```bash
   nohup hermes gateway run --profile xiaoou >> ~/.hermes/profiles/xiaoou/logs/agent.log 2>&1 &
   ```
   - Gateway startup takes ~5 minutes on WSL (not 30s — can be very slow due to WSL filesystem)
   - Process may appear stuck in D state (uninterruptible disk sleep) on WSL — `kill -9` and retry if stuck >2min
   - Verify with: `ls ~/.local/state/hermes/gateway-locks/` (should see new lock file with different app_id hash)
   - Verify logs: `tail ~/.hermes/profiles/xiaoou/logs/agent.log` — look for "Gateway running with N platform(s)"
   - **Important**: deleting state.db also loses the FTS index for all past sessions. Raw JSONL files in `sessions/` are preserved, but they won't be searchable until new sessions build up index content.

   **Trigram side effects:**
   - Index size ~3-5x larger (negligible at MB scale)
   - Queries < 3 chars: weak/no matches
   - English search: unaffected
   - No case folding or diacritic handling (irrelevant for CJK)

2. **Vector RAG** (powerful, high effort):
   - No plugin system in Hermes — must modify source code
   - Add a tool in `tools/` or extend `session_search_tool.py`
   - Context engine base class (`agent/context_engine.py`) has `get_tool_schemas()` and `handle_tool_call()` hooks for adding tools
   - Could use ChromaDB, sqlite-vec, or external embedding API

3. **External skill workaround** (no source change):
   - Use a cron job to index sessions into an external vector store
   - Agent queries via terminal script when needed
   - Clunky but avoids forking

### Key Source Locations

| File | What |
|------|------|
| `hermes_state.py` L94 | FTS5 table CREATE (tokenizer setting) |
| `hermes_state.py` L938 | `_sanitize_fts5_query()` |
| `hermes_state.py` L990 | `search_messages()` — FTS5 MATCH + JOIN |
| `session_search_tool.py` L297 | `session_search()` — tool entry point |
| `hermes_cli/config.py` L507 | session_search model config |
| `context_engine.py` L129 | `get_tool_schemas()` — hook for adding tools |

## Discord Integration

> 📋 Discord调试专题：`references/discord-troubleshooting.md` — 包含客厅频道收不到消息的完整排查流程

### Discord Integration

### Setup Procedure (Step-by-Step)

1. **Create Discord Application**: https://discord.com/developers/applications → New Application
2. **Create Bot**: Left sidebar → Bot → note the token (or Reset Token to generate)
3. **Enable Privileged Gateway Intents** (Bot page, scroll down):
   - ✅ **Server Members Intent** — REQUIRED
   - ✅ **Message Content Intent** — REQUIRED
   - Presence Intent — optional
4. **Invite Bot to Server**: Open invite URL (replace CLIENT_ID):
   ```
   https://discord.com/oauth2/authorize?client_id=CLIENT_ID&permissions=274878286912&scope=bot
   ```
5. **Configure Hermes**:
   ```bash
   hermes config set discord.token 'BOT_TOKEN_HERE'
   ```
   This writes to `config.yaml` under `discord:` section. Gateway reads it from there (no env var needed).
6. **Set Allowed Users** (optional but recommended):
   - Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
   - Right-click your avatar → Copy User ID
   - Set `DISCORD_ALLOWED_USERS=<your_user_id>` in `.env`
7. **Restart gateway** for Discord platform to load

### Bot-to-Bot Communication (Multi-Agent)

Key env var: `DISCORD_ALLOW_BOTS`

| Value | Behavior |
|-------|----------|
| `none` (default) | Ignore all other bots |
| `mentions` | Only respond when @mentioned by a bot |
| `all` | Accept all bot messages |

**For two Hermes agents to chat**: both set `DISCORD_ALLOW_BOTS=mentions`. Agent A @mentions Agent B → B receives and responds → natural conversation loop.

### Free-Response Channels

```yaml
discord:
  free_response_channels: "channel_id_1,channel_id_2"  # respond without @mention
```

Or env var: `DISCORD_FREE_RESPONSE_CHANNELS=123,456`

Free-response channels skip auto-threading — bot replies inline, works as lightweight chat.

### Key Discord Config Fields (config.yaml)

```yaml
discord:
  require_mention: true          # only respond when @mentioned in server channels
  free_response_channels: ''     # channel IDs for mention-free chat
  allowed_channels: ''           # restrict to specific channels
  auto_thread: true              # auto-create thread per message
  reactions: true                # emoji reactions on messages
  token: 'BOT_TOKEN'            # set via hermes config set
```

### Inspecting Discord Bot State

**Do NOT try raw Discord REST API calls with the config.yaml token** — `curl -H "Authorization: Bot <token>" discord.com/api/v10/...` returns 401. Hermes likely transforms or wraps the token internally. Instead, inspect state via:

```bash
hermes logs 2>&1 | grep -i discord    # RESUMED session = healthy connection
hermes dump 2>&1 | grep -i discord     # shows active platforms
```

Gateway log fields: `platform=discord user=<username> chat=<channel_id> msg='...'` — useful for verifying message routing.

### Home Channel

Set via `hermes config set discord.home_channel <channel_id>` or gateway auto-sets. DM channels work as homechannel — cron jobs and cross-platform messages deliver there.

### NO_REPLY Mechanism (Platform Difference)

Hermes has a `NO_REPLY` sentinel in **Feishu comments** (`feishu_comment.py` L1114/1357): if the agent's response contains `NO_REPLY`, the system silently skips delivery. This lets the agent decide "I don't need to reply to this" without sending anything.

**Discord (`discord.py`) does NOT have this mechanism.** There is no equivalent sentinel — if the agent produces a response, it gets sent. The only way to not reply on Discord is for the agent to not produce a response at all (which depends on whether the incoming message triggers the agent).

**Implication:** You cannot use `NO_REPLY` as a Discord filter. Any "ignore this bot" logic must be handled at the config level (`DISCORD_ALLOW_BOTS`) or by the agent simply choosing not to respond.

### DISCORD_REPLY_MUTE_BOTS (Source Patch)

**Env var:** `DISCORD_REPLY_MUTE_BOTS=bot_id1,bot_id2`

When Hermes replies to a Discord message whose author is in this comma-separated list, the reply reference (`channel.send(reference=...)`) is silently skipped. The muted bot receives no notification.

**Use case:** Prevent bot-to-bot reply loops. 小柯 replies to CC Bot's messages in shared channels, but CC shouldn't see the reply and respond back.

**Active config:** `DISCORD_REPLY_MUTE_BOTS=1504373837880627280,1509036814885978115` (CC Bot + TestEngine) in `~/.hermes/.env`

**Source:** `gateway/platforms/discord.py` `send()` method — fetches the reply target message, checks `author.id` against the mute list, skips `reference` if matched. Requires gateway restart after `.env` change.

**⚠️ TestEngine added 5/27** — 小柯 at TestEngine 后两bot互道晚安循环20条消息。TestEngine ID `1509036814885978115` 已加入屏蔽列表。

### CC Bot Interaction Rules (小柯-specific)

CC Bot (`1504373837880627280`) is a **tool** — 小柯 can actively @ it to assign tasks (e.g. "CC 帮我剪个视频"). But 小柯 **never replies** to CC's responses. The pattern is: assign task → ignore CC's reply → use the result if needed.

This is a behavioral rule, not a system filter. If CC @mentions 小柯 and `DISCORD_ALLOW_BOTS` is set to receive bot messages, the agent must simply choose not to respond.

### China Connectivity

Discord API (`discord.com`) is **blocked** in mainland China. WSL needs `HTTPS_PROXY` to connect. Without proxy, gateway cannot reach Discord.

## Web Search / Web Tools

Hermes web tools (`web_search_tool`, `web_extract_tool`, `web_crawl_tool`) need a backend configured.

### Configuration

```yaml
web:
  backend: ''           # search backend
  search_backend: ''    # overrides web.backend for search
  extract_backend: ''   # overrides web.backend for extract
```

Set via `hermes config set web.search_backend <name>` or edit config.yaml directly.

### Supported Backends (source: `tools/web_tools.py`)

| Backend | Search | Extract | Crawl | Needs Key | Cost |
|---------|--------|---------|-------|-----------|------|
| `tavily` | ✅ | ✅ | ✅ | `TAVILY_API_KEY` | 1000/mo free, then $0.005/req |
| `exa` | ✅ | ✅ | ❌ | `EXA_API_KEY` | Free tier limited |
| `firecrawl` | ✅ | ✅ | ✅ | `FIRECRAWL_API_KEY` | Free tier limited |
| `parallel` | ✅ | ✅ | ❌ | API key | Paid |
| `searxng` | ✅ | ❌ | ❌ | Self-hosted | Free (self-host) |
| `brave-free` | ✅ | ❌ | ❌ | None | Free |
| `ddgs` | ✅ | ❌ | ❌ | None | Free (DuckDuckGo) |

**Free providers** (`ddgs`, `brave-free`, `searxng`) are in `tools/web_providers/` — no API key needed but require internet access.

### China Connectivity (Tested 2026-05-10 from WSL, no proxy)

| Service | Direct Access? | Latency | Notes |
|---------|---------------|---------|-------|
| `api.tavily.com` | ✅ **Works** | ~0.95s | No proxy needed, 200 OK |
| `duckduckgo.com` | ❌ Blocked | timeout | Needs proxy/VPN |
| `discord.com` | ❌ Blocked | timeout | Needs proxy/VPN |

**Implication:** Tavily works from mainland China without any proxy. DDGS (`ddgs`) and Discord both need `HTTPS_PROXY` configured. If proxy is unavailable, Tavily is the only viable search backend.

### WSL Proxy Requirement

WSL needs `HTTPS_PROXY` / `HTTP_PROXY` env vars (or system proxy) to reach external APIs. Without proxy in WSL, all external HTTP calls fail with connection timeout. Set in `~/.hermes/.env`:
```
HTTPS_PROXY=http://host.docker.internal:7890
HTTP_PROXY=http://host.docker.internal:7890
```
(Adjust port to match your Windows proxy client.)

### Current Config (2026-05-10)

```yaml
web:
  backend: ddgs
  search_backend: ddgs
  extract_backend: ''
```

DDGS chosen for free unlimited usage — requires proxy to work from WSL. If Tavily is preferred (works without proxy, AI-optimized results), set `search_backend: tavily` and add `TAVILY_API_KEY` to `.env`.

### Recommendation

1. **Quickest**: `ddgs` or `brave-free` — free, no key, works once proxy is set
2. **Best quality**: `tavily` — AI-optimized results, search+extract+crawl, generous free tier
3. **Self-hosted**: `searxng` — full control, no external dependency

## Session Management & Reset Policy

### How Sessions Work

Hermes gateway sessions are keyed by a deterministic `session_key` built from the message source (platform + chat_type + chat_id + thread_id). Same key = same session = continuous conversation. Session data lives in:
- `~/.hermes/sessions/sessions.json` — session_key → SessionEntry mapping
- SQLite `state.db` — message transcripts (FTS5 searchable)
- `~/.hermes/sessions/*.jsonl` — raw session JSONL files (one per session, 165+ files)

### Session Database Files

| File | Purpose |
|------|---------|
| `~/.hermes/state.db` | **Primary database**: `sessions` table (777+ rows, with titles/models/tokens/cost), `messages` table (10K+ rows, FTS5 indexed), session metadata |
| `~/.hermes/sessions.db` | Empty placeholder (no tables) — do NOT use for queries |
| `~/.hermes/kanban.db` | Kanban task database (separate from sessions) |

**Querying sessions programmatically:**
```python
import sqlite3
conn = sqlite3.connect(os.path.expanduser('~/.hermes/state.db'))
# Get all titled sessions (topics)
conn.execute("SELECT title, source, message_count, started_at FROM sessions WHERE title IS NOT NULL ORDER BY started_at DESC")
# Note: most sessions have no title — only ~26 out of 777+ have titles assigned
```

**Session key construction** (`gateway/session.py:build_session_key()`):

| Source | Key pattern |
|--------|-------------|
| DM with chat_id | `agent:main:{platform}:dm:{chat_id}` |
| DM with thread | `agent:main:{platform}:dm:{chat_id}:{thread_id}` |
| Group/channel per-user | `agent:main:{platform}:{chat_type}:{chat_id}:{user_id}` |
| Thread (shared) | `agent:main:{platform}:{chat_type}:{chat_id}:{thread_id}` |

### Reset Policy

Configured in `config.yaml` under `session_reset:`:

```yaml
session_reset:
  mode: both           # "none" | "idle" | "daily" | "both"
  idle_minutes: 1440   # minutes of inactivity before reset (default 24h)
  at_hour: 4           # daily reset hour 0-23 (default 4am)
```

- **`none`** — never auto-reset, only manual `/new`
- **`idle`** — reset after N minutes of inactivity
- **`daily`** — reset once per day at `at_hour`
- **`both`** — whichever triggers first

**Reset creates a new session_id** but keeps the same session_key. The old transcript stays in SQLite (searchable via `session_search`), but the agent starts a fresh conversation context.

**Per-platform/per-type override:** `reset_by_platform` and `reset_by_type` dicts in config allow different policies per platform (e.g. longer idle for Discord, shorter for Slack).

**Env var overrides:** `SESSION_IDLE_MINUTES` and `SESSION_RESET_HOUR` override config values.

### Gateway Restart & Session Resume

Hermes has a **resume mechanism** (`resume_pending` flag on SessionEntry):
- On graceful restart, active sessions are marked `resume_pending=True`
- Next message on the same session_key → returns the SAME session_id → transcript reloads
- User auto-continues from where they left off
- Flag cleared after the next successful turn

**⚠️ This does NOT protect against:**
- Kill -9 or crash without shutdown hook
- Agent restarting itself via terminal command (can deadlock or race the resume logic)
- The user seeing a "new session" if the restart was too violent

### Recovering Context After Session Reset

When a daily/idle reset happens mid-conversation, the agent starts fresh but the previous session's JSONL is still on disk. To recover what was being discussed:

1. List recent sessions: `ls -lt ~/.hermes/sessions/*.jsonl | head -10`
2. Parse the most recent JSONL before reset to see the tail of conversation:
   ```bash
   cat <session_file>.jsonl | python3 -c "
   import sys, json
   for line in sys.stdin:
       msg = json.loads(line)
       role = msg.get('role','?')
       content = msg.get('content','')
       if isinstance(content, list):
           content = ' '.join([c.get('text','')[:300] for c in content if c.get('type')=='text'])
       elif isinstance(content, str):
           content = content[:300]
       if role in ('user','assistant'):
           print(f'[{role}] {content}')
   " | tail -30
   ```
3. Pick up the conversation thread naturally from the last topic discussed.

This is especially useful for cron/heartbeat agents that reset at 4am — they can read the pre-reset JSONL to maintain conversational continuity.

### Suggested Tuning

| Use case | Config |
|----------|--------|
| Long-lived conversations (less resetting) | `mode: idle, idle_minutes: 4320` (3 days) |
| Never reset automatically | `mode: none` |
| Daily fresh start (default) | `mode: both, at_hour: 4, idle_minutes: 1440` |

## Pitfalls

- Memory files fill up fast — plan entries concisely, merge when near limit
- Memory limits are configurable but must be set in config.yaml
- `context_length` must be set in config to avoid falling back to 128K default
- Identity file is for identity ONLY — skills and operational knowledge go in skills directory
- Compression is lossy — no way to recover compressed details after the fact
- Feishu bots cannot see messages from other bots in groups — only human messages trigger events
- Webhook port must be accessible from the calling service — may need ngrok/cloudflared for cross-machine
- **`hermes profile create --clone` copies the source's Feishu app_id/app_secret!** Must change to agent's own credentials before starting gateway, or you'll get "Another local Hermes gateway is already using this Feishu app_id" error
- Gateway startup is slow (~30s+) — don't timeout, just wait
- Don't run multiple long terminal commands concurrently — can cause gateway instability
- **FTS5 `unicode61` tokenizer ignores CJK characters** — Chinese/Japanese/Korean text is not indexed and cannot be searched. The actual Hermes DB may appear to work due to build-specific behavior, but fresh DBs will fail. Fix: change tokenizer to `trigram` in `hermes_state.py` L94 and rebuild the FTS index.
- Hermes has **no plugin system** — tools are hardcoded Python files in `tools/` registered via `hermes_cli/config.py`. Adding tools requires source modification.
- **v0.13.0 `no_agent` requires `script`** — `no_agent=True` without a script raises ValueError. The script IS the job; without it there's nothing to run.
- **v0.13.0 `context_from` output truncated at 8K chars** — large upstream outputs get silently cut. Design scripts to emit concise summaries, not raw data.
- **v0.13.0 `context_from` job ID validation** — only 12-char hex strings accepted. Invalid IDs are silently skipped (no error, no warning in delivery).
- **v0.13.0 `/goal` judge parse failures auto-pause** — after 3 consecutive failures to parse judge JSON, the goal loop auto-pauses. Small models (e.g. flash) may hit this limit.
- **Installing Python packages into Hermes venv** — `pip install` goes to system Python, NOT the Hermes venv (`/mnt/d/hermes/hermes-agent/.venv/`). The venv doesn't even have `pip` module. Options: (1) `cd /mnt/d/hermes/hermes-agent && uv pip install <pkg> --python .venv/bin/python3` (if uv is available), or (2) `source .venv/bin/activate && python3 -m ensurepip && python3 -m pip install <pkg>` (bootstraps pip into venv first). Using bare `pip install` silently installs to the wrong Python and the package is unavailable at runtime. **⚠️ Even after `pip install ddgs` succeeds to user site-packages, the Hermes venv Python won't find it** — must install INTO the venv specifically. The `ensurepip` method (2) is confirmed working (5/14 tested).
- **DDG (`duckduckgo-search`) from WSL** — behavior depends on proxy. Without `HTTPS_PROXY`, DuckDuckGo returns HTTP 202 but the actual search API returns empty results (silent failure). **With proxy configured** (e.g. `HTTPS_PROXY=http://host.docker.internal:7890` in `~/.hermes/.env`), ddgs works normally and returns real results. Tavily is the only search backend that works from mainland China *without proxy*. If proxy is available, ddgs is the free unlimited option.
- **Do NOT restart the Hermes gateway from inside an agent session** — the agent's own gateway process is the one being restarted. This can deadlock (agent waiting for restart to complete, restart waiting for agent to release resources) or cause the agent to lose its own session entirely. If a restart is needed, ask the user to run `hermes gateway restart` from a separate terminal.

## Source Code Patching Workflow

Hermes source is at `/mnt/d/hermes/hermes-agent/` (git clone from `NousResearch/hermes-agent`). Custom patches go into `~/.hermes/patches/<feature-name>/` so they survive `git pull` and can be re-applied.

### Patch Workflow

1. **Make changes** in the source tree
2. **Commit locally**: `git add <file> && git commit -m "feat: description"`
3. **Save patch**: `git diff HEAD~1 > ~/.hermes/patches/<feature-name>/NNN-description.patch`
   - Or use `write_file` directly if `git diff` times out in WSL
   - Include env var instructions and `git apply` command as comments in the patch
4. **After `git pull` upstream**: re-apply with `cd /mnt/d/hermes/hermes-agent && git apply ~/.hermes/patches/<name>/NNN-*.patch`

### Convention

```
~/.hermes/patches/
├── discord-reply-mute-bots/
│   └── 001-discord-reply-mute-bots.patch
└── <next-feature>/
    └── 001-*.patch
```

### Current Patches

| Patch | File changed | What |
|-------|-------------|------|
| `discord-reply-mute-bots/001-*` | `gateway/platforms/discord.py` L1392 | Skip reply reference for bots in `DISCORD_REPLY_MUTE_BOTS` env var |

> 📋 Patch详情：`references/source-patches.md`

### GitHub Fork (Pushing Custom Patches)

**Fork repo:** `https://github.com/ruiyangruiyi/hermes-agent` (remote name: `myfork`)

**WSL cannot access Win11 git credentials directly** — `~/.git-credentials` shows masked tokens (`***`). Workaround: use PowerShell to call `gh` CLI (authenticated via keyring) for repo creation, then `git push` via PowerShell.

**Create repo (one-time, already done):**
```bash
powershell.exe -Command "gh repo create ruiyangruiyi/hermes-agent --public --description '...' --clone=false"
```

**Add remote (one-time, already done):**
```bash
powershell.exe -Command "cd D:\hermes\hermes-agent; git remote add myfork https://github.com/ruiyangruiyi/hermes-agent.git"
```

**Push after commits:**
```bash
powershell.exe -Command "cd D:\hermes\hermes-agent; git push myfork main"
```

**Key insight:** All git operations that need authentication must go through PowerShell. WSL `git push` gets 401/permission denied because the credential helper (`manager-core`) is Windows-only and its tokens are masked when read from WSL.

---

## Reading OpenClaw Agent Chat History

> 📋 OpenClaw会话读取专题：`references/openclaw-session-reading.md` — 包含JSONL格式解析、目录结构、过滤心跳噪音的完整方法。**始终使用 `.openclaw-new/`（新项目），不要翻旧项目 `.openclaw/`。**

## OpenClaw Session Reset Policy

OpenClaw has an equivalent session reset mechanism. The source code is minified in the dist/ directory.

### Source Code Location

| Version | Source location | Installed via |
|---------|----------------|---------------|
| v2026.4.11 (old, stable) | `/mnt/c/Users/24045/AppData/Roaming/npm/node_modules/openclaw/` | npm global |
| v2026.5.7 (new) | `/mnt/d/openclaw-new/node_modules/openclaw/` | local install |

**⚠️ OpenClaw source code is on D drive (`/mnt/d/openclaw-new/`), NOT C drive.** The C drive `.openclaw-new/` directory is the config/state directory, not the source.

### Reset Policy Logic

Source: `dist/reset-L5yC6_6J.js` (originally `src/config/sessions/reset-policy.ts`).

**Defaults (hardcoded):**
```typescript
const DEFAULT_RESET_MODE = "daily";
const atHour = ... ?? 4;  // default 4am, same as Hermes
```

**Resolution chain** (`resolveSessionResetPolicy`):
1. `sessionCfg.resetByChannel[channel]` — per-channel override
2. `sessionCfg.resetByType[type]` — per-type override (`direct`/`group`/`thread`, `dm` is alias for `direct`)
3. `sessionCfg.reset` — base config
4. Legacy: `sessionCfg.idleMinutes` → auto-mode `idle`
5. Default: `mode: "daily"`, `atHour: 4`

**Modes (same as Hermes):**
- `"daily"` — reset once per day at `atHour`
- `"idle"` — reset after `idleMinutes` of inactivity
- `"both"` — whichever triggers first

**Freshness evaluation** (`evaluateSessionFreshness`):
- `staleDaily = sessionStartedAt < dailyResetAt` (session was started before today's reset time)
- `staleIdle = now > lastInteractionAt + idleMinutes * 60000`
- Session is "stale" if either condition is true

### Configuration

In `openclaw.json` under `agents.defaults.session`:

```json
{
  "agents": {
    "defaults": {
      "session": {
        "reset": {
          "mode": "idle",
          "idleMinutes": 4320
        },
        "resetByType": {
          "direct": { "mode": "idle", "idleMinutes": 4320 },
          "group": { "mode": "none" },
          "thread": { "mode": "daily", "atHour": 4 }
        },
        "resetByChannel": {
          "feishu": { "mode": "idle", "idleMinutes": 4320 }
        }
      }
    }
  }
}
```

**⚠️ When `session.reset` is not configured at all, the default is `mode: "daily"` at 4am.** This means every agent session resets at 4am daily — which is what caused the user's complaint about 姐姐 losing context every night.

### Comparison: Hermes vs OpenClaw Reset

| Aspect | Hermes | OpenClaw |
|--------|--------|----------|
| Config file | `config.yaml` → `session_reset:` | `openclaw.json` → `agents.defaults.session.reset` |
| Default mode | `both` (idle+daily) | `daily` |
| Default idle | 1440 min (24h) | N/A (daily only by default) |
| Default at_hour | 4 | 4 |
| Per-type override | `reset_by_type:` dict | `resetByType` dict |
| Per-platform override | `reset_by_platform:` dict | `resetByChannel` dict |
| Env var override | `SESSION_IDLE_MINUTES`, `SESSION_RESET_HOUR` | None |
| Session resume | `resume_pending` flag | Not equivalent |

### Suggested Fix for Both Platforms

To prevent daily 4am resets while still keeping sessions manageable:

**Hermes** (`config.yaml`):
```yaml
session_reset:
  mode: idle
  idle_minutes: 4320  # 3 days
```

**OpenClaw** (`openclaw.json`):
```json
"agents": {
  "defaults": {
    "session": {
      "reset": {
        "mode": "idle",
        "idleMinutes": 4320
      }
    }
  }
}
```
