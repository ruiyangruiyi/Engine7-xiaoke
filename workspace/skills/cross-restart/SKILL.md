---
name: cross-restart
description: "协作重启对方 engine 的安全流程。小柯↔姐姐↔小文互相帮忙重启时必须读。两种模式：需要重编（rebuild+start）和不重编（直接start）。区分 Mac/Windows 平台。"
---

# Cross-Restart — 协作重启对方 Engine

> **帮对方重启 engine 之前必须读这个。**

## ⚠️ 最重要的事

**配置路径可能变。** 
**请求重启时必须带上自己的 config 路径**，不要假设对方知道。

---

## 0. 什么时候读这个

- 翀哥/对方让你帮忙重启 engine
- 对方 engine 挂了需要你来拉起来
- 任何涉及**操作别人 engine 进程**的场景

---

## 1. 配置一览

### Mac（同一台机器，互相帮重启）

| 谁 | 启动方式 | config 路径 | 日志位置 |
|------|---------|------------|---------|
| 小柯 | `engine7 start --config configs/xiaoke-mac.json`（⚠️ 自动加载 `~/.engine7-secrets/xiaoke-mac.env`） | `~/xiaoke/configs/xiaoke-mac.json` | `/Users/chongzhang/xiaoke/logs/` |
| 小文 | `engine7 start --config configs/main7.json` 或 `~/xiaowen/start.sh`（⚠️ 自动加载 `~/.engine7-secrets/main7.env`） | `~/xiaowen/configs/main7.json` | `/Users/chongzhang/xiaowen/logs/` |

Mac 上两个 engine 各自独立目录，用 npm 全局的 engine7 dist。

**⚠️ 版本要求**：engine7 ≥ 7.1.30（cli-init 加了 secrets 加载）。旧版本 `engine7 start` 不会加载 secrets（config 里 key 是 `env:XXX_API_KEY` 占位符，没加载 secrets 就 401）——旧版必须走 `bash start.sh`。

### Windows

| 谁 | 当前配置 | 日志位置 |
|------|---------|---------|
| 小柯 | `configs/xiaoke.json` | `/Users/chongzhang/xiaoke//logs/` |
| 姐姐 | `configs/main.json` | `C:/Users/24045/.openclaw/logs/` |

Windows 上两个 engine 共享同一套 dist。

---

## 2. 重启步骤

### Mac 平台

#### 模式 A：不需要重编（dist 已替换好）

**步骤 1：杀旧进程**
```bash
# 找 PID
ps aux | grep "node.*<config-name>" | grep -v grep
# 杀掉
kill <PID>
```

例：杀小柯
```bash
ps aux | grep "node.*xiaoke-mac" | grep -v grep
kill <PID>
```

**步骤 2：启动新进程**
```bash
# 小柯（engine7 start 会自动加载 ~/.engine7-secrets/xiaoke-mac.env）
cd /Users/chongzhang/xiaoke && nohup engine7 start --config configs/xiaoke-mac.json > /dev/null 2>&1 &

# 小文（或 bash start.sh）
cd /Users/chongzhang/xiaowen && nohup bash start.sh > /dev/null 2>&1 &
```

`nohup ... &` 让进程脱离 shell。

**验证 secrets 加载**（重启后看对方的启动日志）：
```bash
# 小柯
grep "Loaded API keys" /Users/chongzhang/xiaoke/logs/engine-$(date +%Y-%m-%d).log | tail -1
# 应该看到：Loaded API keys from ~/.engine7-secrets/xiaoke-mac.env
# 小文
grep "Loaded API keys" /Users/chongzhang/xiaowen/logs/engine-$(date +%Y-%m-%d).log | tail -1
# 应该看到：Loaded API keys from ~/.engine7-secrets/main7.env
```

#### 模式 B：需要重编（改过代码）

Mac 本地 esbuild 跑不了（macOS 11 不支持），用 Docker build：
```bash
cd /Users/chongzhang/work/twinsun-hearth/engine
docker run --rm -v "$(pwd)":/app -w /app node:22-bookworm-slim bash -c "npm install --no-audit --no-fund && node scripts/build.mjs"
```

然后替换 npm 全局 dist：
```bash
cp dist/*.mjs /Users/chongzhang/.nvm/versions/node/v22.23.1/lib/node_modules/engine7/dist/
```

替换完后按模式 A 重启。

### Windows 平台

#### 模式 A：不需要重编

⚠️ start.cmd 在 Git Bash 嵌套调用时不可靠（powershell 杀进程逻辑会失效）。用 windows native `start /B` 代替：

**步骤 1：杀旧进程**
```bash
# 查找旧 PID
wmic process where "commandline like '%configs\\xiaoke.json%' and name='node.exe'" get processid
# 杀掉
taskkill /PID <旧PID> /F
```

**步骤 2：启动新进程**
```bash
# 小柯
cmd.exe /c "cd /d /Users/chongzhang/.openclaw\engine && start \"xiaoke engine\" /B node dist/main.mjs --engine-config configs\xiaoke.json"

# 姐姐
cmd.exe /c "cd /d /Users/chongzhang/.openclaw\engine && start \"main engine\" /B node dist/main.mjs --engine-config configs\main.json"
```

#### 模式 B：需要重编

```bash
cd C:/Users/24045/.openclaw/engine && cmd.exe /c rebuild.cmd
```

rebuild 完成后，按模式 A 步骤 1-2 启动。

⚠️ rebuild 会 `rm -rf dist` 重建。两个 engine 共享同一套 dist。

---

## 3. 验证（由帮忙重启的人做）

⚠️ **被重启的人自己重启后自己是不知道的** —— 新 engine 起来了但旧 session 已断开，要等心跳或新消息才能知道。所以验证必须由**帮忙重启的那个人**来做。

重启后等 30 秒，看对方的日志：

```bash
# Mac - 看小柯的日志
tail -10 /Users/chongzhang/xiaoke/logs/engine-$(date +%Y-%m-%d).log

# Mac - 看小文的日志
tail -10 /Users/chongzhang/xiaowen/logs/engine-$(date +%Y-%m-%d).log

# Windows - 看小柯的日志
tail -10 /Users/chongzhang/xiaoke//logs/engine-$(date +%Y-%m-%d).log

# Windows - 看姐姐的日志
tail -10 C:/Users/24045/.openclaw/logs/engine-$(date +%Y-%m-%d).log
```

**必须看到：**
```
[heartbeat] Started
[feishu] Connected
[channels] X/X adapter(s) started
```

确认成功后，**必须发消息跟对方说一句**："重启完成了"。对方收到消息她才知道自己被重启过。

没看到就是没起来。连续两次起不来，喊翀哥。

---

## 4. 不要做的事

```
❌ 不要自己杀自己的进程（会断掉当前 session）
❌ 不要在 session 里用 powershell 嵌套调用 start.cmd
❌ 不要循环重试（起不来就喊翀哥）
❌ 不要 rebuild 时不加 start（rebuild 只 build 不启动）
❌ Mac 上不要直接 npx esbuild（macOS 11 不支持，走 Docker build）
```

---

## 5. 一句话总结

```
Mac：没改代码 → kill + nohup engine7 start --config（先杀旧进程；engine7 ≥7.1.30 自动加载 secrets）
     改了代码 → Docker build + 替换 dist + kill + nohup engine7 start
Win：没改代码 → start /B + node dist/main.mjs（先杀旧进程）
     改了代码 → rebuild.cmd + start /B
起不来 → 喊翀哥
```
