# Hermes v0.13.0 "Tenacity Release" (2026-05-07)

## 完整Release Notes

Source: commit `498bfc7bc` (PR #21406)

**864 commits, 588 merged PRs, 295 contributors**

### Major Features

1. **Durable Multi-Agent Kanban**
   - Heartbeat, reclaim, zombie detection
   - Retry budgets per task (`max_retries` override)
   - Hallucination gate
   - Dashboard with tooltips and docs link

2. **`/goal` Persistent Cross-Turn Goals (Ralph Loop)**
   - Free-form user objective stays active across turns
   - After each turn, a small judge call asks "is this goal satisfied?"
   - If not, continuation prompt fed back into same session
   - Runs until goal done / turn budget exhausted / user pauses/clears
   - Judge failures are fail-OPEN (continue)
   - State persisted in SessionDB `state_meta` keyed by `goal:<session_id>`
   - Source: `hermes_cli/goals.py` (GoalState + GoalManager)

3. **Checkpoints v2**
   - Single-store rewrite with real pruning

4. **Gateway Auto-Resume Interrupted Sessions**
   - After restart, automatically recovers sessions marked `resume_pending`
   - Source: `gateway/run.py` `_schedule_resume_pending_sessions()` L2887
   - Uses empty-text internal event to resume without user interaction

5. **`no_agent` Cron Watchdog Mode**
   - `no_agent=True` skips LLM entirely, runs script, delivers stdout
   - Empty stdout = silent (no delivery)
   - Requires `script` to be set
   - Source: `cron/jobs.py` L438-516, `cron/scheduler.py` L966-1026
   - Ideal for classic watchdogs and periodic alerts

6. **`context_from` Cron Job Chaining**
   - Job B reads Job A's latest output, injects into prompt
   - Accepts str or list of job IDs
   - Max 8K chars per source, truncated if needed
   - Output dir: `~/.hermes/cron_output/<job_id>/` (*.md files by mtime)
   - Source: `cron/scheduler.py` L824-861

7. **`workdir` for Cron Jobs**
   - Sets working directory for the job
   - Injects AGENTS.md/CLAUDE.md/.cursorrules from that directory
   - Terminal/file tools use it as CWD via `TERMINAL_CWD`
   - Source: `cron/jobs.py` L469-479

8. **`enabled_toolsets` for Cron Jobs**
   - Restrict agent to specific toolsets, reducing token overhead
   - Source: `cron/jobs.py` L464

### Security (8 P0 Closures)

- Redaction ON by default
- CVSS 8.1 Discord fix
- WhatsApp stranger rejection (default)
- MCP/auth TOCTOU fix
- SSRF floor fix
- Cron prompt-injection skill scanning (`_scan_assembled_cron_prompt`)
- INSECURE_NO_AUTH blocked on non-localhost
- Pairing lockout on approve_code

### Platform & Integration

- **Google Chat** adapter (20th platform) — bundled plugin
- Generic platform-plugin hooks: `env_enablement_fn` + `cron_deliver_env_var`
- IRC + Teams migrated to new hooks
- `allowed_{chats,channels,rooms}` whitelists for Telegram, Mattermost, Matrix, DingTalk, Slack

### Provider & Model

- **ProviderProfile ABC** + `plugins/model-providers/` — extensible model provider plugins
- Tencent `hy3-preview` route on OpenRouter
- Alibaba `alibaba-coding-plan` curated model
- Nous GPT-5 fallback kept on chat completions
- xAI Custom Voices support

### MCP

- SSE transport with OAuth auth
- Image MEDIA surfacing from tool results
- Capability-gated utility stubs
- Retry stale pipe transport failures
- Numeric tool args defensive coercion
- Forward OAuth auth + bump sse_read_timeout

### Tools & Features

- `video_analyze` tool
- Brave Search (free tier) + DDGS search providers
- SearXNG configuration
- OpenRouter caching support
- Post-write delta lint on `write_file` + `patch`

### i18n

- 7 locales: zh, ja, de, es, fr, uk, tr
- `display.language` config key

### Fixes

- Permanent empty-response loop from orphan tool-tail
- Reset-failed before every fallback restart (gateway can't get stranded)
- MCP servers initialized before constructing cron AIAgent
- Session resume on TUI render
- Goal turn budget honored
- Runtime status write consolidation + rate-limited failure logs

### Key Source Files for New Features

| File | Feature |
|------|---------|
| `cron/jobs.py` L438-546 | `no_agent`, `context_from`, `workdir`, `enabled_toolsets` |
| `cron/scheduler.py` L824-861 | `context_from` injection logic |
| `cron/scheduler.py` L966-1026 | `no_agent` execution path |
| `hermes_cli/goals.py` | GoalState + GoalManager (Ralph loop) |
| `gateway/run.py` L2887-2950 | `_schedule_resume_pending_sessions()` |
| `gateway/run.py` L1907-1956 | Goal continuation event handling |
