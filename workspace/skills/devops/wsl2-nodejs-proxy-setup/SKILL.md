---
name: WSL2 Node.js + Proxy Setup
description: Key pitfalls when installing nvm/Node.js in WSL2 and routing through Windows proxy
type: reference
---

# WSL2 Node.js + Proxy Setup

Key lessons from setting up Node.js and npm in WSL2 behind Windows Clash proxy.

## WSL2 Cannot Reach Windows via localhost

WSL2 is a VM — `127.0.0.1` refers to the Linux VM, not Windows. Find the Windows host IP:

```bash
ip route show default | awk '{print $3}'
```

## Windows Proxy Must Allow LAN Connections

Two prerequisites on the Windows side:
1. Clash for Windows → General → enable **"Allow LAN"**
2. Windows Firewall must allow inbound TCP on proxy port — add a firewall rule via PowerShell (Admin)

## Use Chinese Mirrors for nvm and Node.js

GitHub and npmjs.org are slow or unreachable from China without proxy. Use mirrors instead:
- nvm: gitee.com/mirrors/nvm (instead of github.com/nvm-sh/nvm)
- Node.js binary: set `NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node`
- npm packages: use `--registry=https://registry.npmmirror.com` for domestic packages

## npm ENOTEMPTY Error

If a previous npm install was interrupted, it leaves partial files. Delete the partial module directory before retrying.

## Proxy Only When Needed

Unset proxy vars when downloading from Chinese mirrors (Gitee, npmmirror) — routing domestic traffic through proxy is slower and unnecessary.

## TUN Mode is Simplest

If Clash for Windows has TUN mode enabled, all WSL2 traffic automatically goes through the proxy. No need to manually set `http_proxy`/`https_proxy` environment variables. This is the easiest approach when available.

## Windows-Side npm Packages Don't Work in WSL2

If Claude Code (or other npm packages) are installed on the Windows side (`/mnt/c/Users/.../npm/claude`), running them in WSL2 will fail with `exec: node: not found` because WSL2 has no Node.js in its own PATH. Fix: install nvm + Node.js natively inside WSL2, then `npm install -g` there.

## Claude Code Plugin Installation in WSL2

Settings and plugins live at `~/.claude/`. Key files:
- `~/.claude/settings.json` — API keys, model mappings, env vars, enabled plugins
- `~/.claude/plugins/` — marketplace cache, installed plugins metadata

### Adding the Official Marketplace

```bash
# Requires proxy for GitHub access
export https_proxy=http://$(ip route show default | awk '{print $3}'):7890
claude plugins marketplace add anthropics/claude-plugins-official
```

### Batch Installing Plugins

Get the plugin list from an existing Windows installation (`/mnt/c/Users/<winuser>/.claude/settings.json` → `enabledPlugins` keys, strip `@claude-plugins-official` suffix). Then loop:

```bash
plugins=( "superpowers" "github" "code-review" "context7" ... )
for p in "${plugins[@]}"; do
  claude plugins install "$p@claude-plugins-official"
done
```

### Troubleshooting

- **"Not logged in"** when running `claude config list` → This is normal if using API key auth (not OAuth). Settings in `settings.json` still work.
- **No marketplaces configured** → Must add marketplace first before installing any plugin.
- **Marketplace source format** → Use GitHub `owner/repo` format: `anthropics/claude-plugins-official`. Bare name won't work.
- Windows-side plugin cache at `/mnt/c/Users/<winuser>/.claude/plugins/known_marketplaces.json` can reveal the marketplace source if you forget the repo name.

## Verifying Proxy Connectivity

Test proxy from WSL2 before attempting installs:
```bash
curl -x http://$(ip route show default | awk '{print $3}'):7890 -I https://www.google.com --connect-timeout 10
```
If this fails with "Connection refused" → check Allow LAN in Clash. If it times out → check Windows Firewall.
