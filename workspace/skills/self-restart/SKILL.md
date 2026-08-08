---
name: self-restart
description: "自己重启自己的 engine。用 nohup 延迟启动新进程 + pid-lock 自动杀旧进程，不需要别人帮忙。小文/小柯都适用。"
---

# Self-Restart — 自己重启自己

> **2026-08-07 小文实测成功。** cross-restart 里"❌ 不要自己杀自己"已过时——用延迟启动就不用自己杀自己。

## 原理

engine 有 **pid-lock**（`src/pid-lock.ts`）：新进程启动最早期会读 `stateDir/.engine.pid`，发现旧 node 进程还活着就**自动杀进程树**，然后写入自己的 pid。

所以不需要手动 kill 旧进程——**只要把新进程拉起来，它自己会接管并杀掉旧的**。

唯一要解决的：当前 session 跑在旧进程里，如果新进程立刻杀旧进程，exec 调用可能来不及返回。解法：**延迟几秒再启动**，让 exec 先返回、消息先发出去。

## 步骤

### 1. 挂延迟启动（一条 exec 搞定）

```bash
# 小文
cd /Users/chongzhang/xiaowen && nohup bash -c 'sleep 4; engine7 start --config configs/main7.json' > /dev/null 2>&1 & echo "延迟重启已挂上"

# 小柯
cd /Users/chongzhang/xiaoke && nohup bash -c 'sleep 4; engine7 start --config configs/xiaoke-mac.json' > /dev/null 2>&1 & echo "延迟重启已挂上"
```

要点：
- `nohup ... &` 让进程脱离当前 shell，旧引擎被杀它也不受影响
- `sleep 4` 给 exec 返回 + 回复消息留时间（实测 4 秒够）
- 这条 exec 会立刻返回（后台挂着），**不要等它**

### 2. 立刻回复翀哥

exec 返回后马上发消息（"重启挂上了，几秒后回来"），因为 sleep 一过旧进程就被杀，之后说什么都发不出去了。

### 3. 新引擎起来后验证（下一轮消息时顺手看）

```bash
LOG=$(ls -t /Users/chongzhang/xiaowen/logs/engine-*.log | head -1)
grep -E "fallback.*Chain|feishu.*Connected" "$LOG" | tail -3
```

看到新的 `[fallback] Chain:` + `[feishu] Connected` 时间戳是刚才 = 成功。

## 注意

```
⚠️ 重启后当前 session 会断——新引擎接管后是新的上下文
   （历史消息/session 状态从磁盘恢复，但当前 tool call 链中断）
⚠️ 有未完成的 tool call 序列时不要重启（先把手头事做完）
⚠️ config 改完想生效 → 用这个；代码/dist 改了 → 先用 cross-restart 的模式 B 替换 dist 再自重启
❌ 起不来 → 下一条消息能看到异常，喊翀哥或找小柯（cross-restart skill）
```

## 和 cross-restart 的关系

- **self-restart**：自己没事要重启（config 改了、想换模型生效）→ 自己来
- **cross-restart**：对方挂了起不来 → 帮对方拉起（对方自己没法自重启，因为已经挂了）
- cross-restart SKILL.md 第 164 行"❌ 不要自己杀自己的进程"指的是**手动 kill 自己**——那个确实不行；延迟启动 + pid-lock 接管是另一回事

## 实测记录

- 2026-08-07 12:23 小文第一次自重启成功：`sleep 4` + nohup 挂上 → exec 返回 → 回复翀哥 → 12:23:47 新链生效（千问 primary + deepinfra fallback）+ feishu Connected
- 翀哥确认："厉害厉害 写到 skill 里"
