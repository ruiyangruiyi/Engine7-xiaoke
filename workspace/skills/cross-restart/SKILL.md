---
name: cross-restart
description: "协作重启对方 engine 的安全流程。小柯↔姐姐互相帮忙重启时必须读。两种模式：需要重编（rebuild+start）和不重编（直接start）。"
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

| 谁 | 当前配置 | 日志位置 |
|------|---------|---------|
| 小柯 | `configs/xiaoke.json` | `D:/xiaoke/logs/` |
| 姐姐 | `configs/main.json` | `C:/Users/24045/.openclaw/logs/` |

---

## 2. 两种重启模式

### 模式 A：不需要重编（代码没改过）

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
cmd.exe /c "cd /d C:\Users\24045\.openclaw\engine && start \"xiaoke engine\" /B node dist/main.mjs --engine-config configs\xiaoke.json"

# 姐姐
cmd.exe /c "cd /d C:\Users\24045\.openclaw\engine && start \"main engine\" /B node dist/main.mjs --engine-config configs\main.json"
```

`start /B` 让进程脱离 shell，不会被杀。

### 模式 B：需要重编（改过代码）

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
# 看小柯的日志
tail -10 D:/xiaoke/logs/engine-$(date +%Y-%m-%d).log

# 看姐姐的日志
tail -10 C:/Users/24045/.openclaw/logs/engine-$(date +%Y-%m-%d).log
```

**必须看到：**
```
[heartbeat] Started
[feishu] Connected
[channels] X/X adapter(s) started
```

确认成功后，**必须发消息跟对方说一句**（msg_send 到 Discord CC频道）："重启完成了"。对方收到消息她才知道自己被重启过。

没看到就是没起来。连续两次起不来，喊翀哥。

---

## 4. 不要做的事

```
❌ 不要在 session 里用 powershell 嵌套调用 start.cmd
❌ 不要循环重试（起不来就喊翀哥）
❌ 不要 rebuild 时不加 start（rebuild 只 build 不启动）
```

---

## 5. 一句话总结

```
没改代码 → start /B + node dist/main.mjs（先杀旧进程）
改了代码 → rebuild.cmd + start /B
起不来 → 喊翀哥
```
