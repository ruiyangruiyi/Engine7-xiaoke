---
name: WSL Browser Setup & Troubleshooting
description: Hermes browser tool in WSL2 — installation steps, CAPTCHA issues, headed mode, and cloud browser alternatives
version: 1.0
---

# WSL Browser Setup & Troubleshooting

## Installation (one-time)

```bash
# 1. Install Chrome via agent-browser
npx agent-browser install

# 2. Install system libraries (need sudo access)
sudo apt-get install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
```

Chrome installs to: `~/.agent-browser/browsers/chrome-{version}/`

## Known Issues

### 1. Search engines block headless browsers
Google, Baidu, Bing ALL detect headless Chrome and show CAPTCHA/verification pages. This is the **biggest blocker** for web search in WSL.

- Google → "unusual traffic" CAPTCHA (unpassable without human)
- Baidu → 图形验证码
- Bing → returns empty results or captcha

### 2. WSLg headed Chrome works but can't share sessions
WSL2 with WSLg supports headed Chrome (DISPLAY=:0, WAYLAND_DISPLAY=wayland-0). Can launch Chrome manually:
```bash
export DISPLAY=:0
~/.agent-browser/browsers/chrome-*/chrome --no-sandbox --remote-debugging-port=9222 "https://example.com" &
```

**BUT**: Hermes browser_navigate tool launches its OWN Chrome instance. Cannot reuse user's logged-in session. Cookies/login NOT shared between instances.

### 3. Network depends on Windows host
If Windows is sleeping or VPN/proxy is down, WSL browser won't reach external sites. Feishu messaging still works (external API, not local browser).

## Cloud Browser Providers

Hermes supports cloud browser providers (see config.yaml browser section) — Browserbase, Browser Use, Firecrawl. These use residential IPs and real fingerprints to bypass CAPTCHAs. Best for public browsing/search, not for sensitive operations (credentials pass through third-party).

## What Works vs What Doesn't

| Task | Local WSL | Cloud Browser |
|------|-----------|---------------|
| Web search | CAPTCHA blocked | Works |
| Browse public pages | Some sites block | Works |
| Login to accounts | Possible but risky | Credentials via 3rd party |
| Read documentation | Often works | Works |
| Social media automation | Gets detected/banned | Better but not foolproof |

## Feishu Bot Limitation

Bots cannot see each other's messages in Feishu groups. Need bridge forwarding for bot-to-bot group communication. Telegram/Discord don't have this limitation.
