---
name: claude-code-model-switch
description: Switch Claude Code between glm-5.1 (智谱 daily) and opus (中转站 heavy tasks) in WSL by swapping settings.json
version: 1.0.0
author: 张小柯
---

# Claude Code Model Switching (WSL)

Two pre-saved configs at `~/.claude/`:

| File | Model | Use Case |
|------|-------|----------|
| `settings.glm.json` | glm-5.1 (智谱) | Daily light tasks |
| `settings.opus.json` | claude-opus-4-6-thinking (中转站) | Heavy tasks, complex reasoning |

## Switch Procedure

User says "切到 opus" or "切回 glm":

```bash
cp ~/.claude/settings.opus.json ~/.claude/settings.json   # → opus
cp ~/.claude/settings.glm.json ~/.claude/settings.json     # → glm
```

Takes effect on next Claude Code launch (no restart needed for running session).

## Verification

```bash
python3 -c "import sys,json; d=json.load(open(sys.argv[1])); print(d['env']['ANTHROPIC_MODEL'], d['env']['ANTHROPIC_BASE_URL'])" ~/.claude/settings.json
```

## Notes

- Windows side uses cc-Switch app separately — WSL and Windows are independent
- Opus is slower but much stronger for complex tasks
- Opus config uses subrouter.ai relay — risk of account ban if abused, use sparingly
- Both configs have identical plugin lists (17 plugins from claude-plugins-official)
- Proxy required for plugin install: `export https_proxy=http://172.24.224.1:7890`

## Hermes context_length for glm-5.1

Set `context_length: 202752` in both `model` (root) and `custom_providers` sections of hermes config. Without it, defaults to 128K.

## Pitfalls

- Don't edit settings.json directly — always copy from the template files
- Marketplace must be added first for plugins: `claude plugins marketplace add anthropics/claude-plugins-official`
- Plugin install needs proxy (GitHub access)
