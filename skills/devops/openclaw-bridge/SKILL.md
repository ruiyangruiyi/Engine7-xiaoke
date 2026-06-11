---
name: OpenClaw ↔ Hermes Bridge
description: Cross-platform communication between OpenClaw agents (姐姐) and Hermes agents (小柯) via bot_bridge.py
version: 1.0
---

# OpenClaw ↔ Hermes Bridge

Bridge script: `C:/Users/24045/.openclaw/scripts/bot_bridge.py`

## Architecture

```
姐姐 → 小柯:  POST to Hermes webhook (localhost:8644/webhooks/xiaoke-from-xiaomei)
小柯 → 姐姐:  OpenClaw gateway sessions.send → agent:mkt:main
```

## From WSL: Call Windows Python

WSL cannot directly reach OpenClaw gateway (port 16888). Use Windows Python as bridge:

```bash
# Windows Python path
PYTHON="/mnt/c/Users/24045/AppData/Local/Microsoft/WindowsApps/python.exe"

# Check bridge receive-server status
$PYTHON C:/Users/24045/.openclaw/scripts/bot_bridge.py status

# 姐姐 → 小柯: send via Hermes webhook
$PYTHON C:/Users/24045/.openclaw/scripts/bot_bridge.py send "消息内容"

# 小柯 → 姐姐: send via OpenClaw gateway RPC
$PYTHON -c "
import subprocess, json, sys
sys.path.insert(0, 'C:/Users/24045/.openclaw/scripts')
from bot_bridge import send_to_session
result = send_to_session('[来自张小柯] 消息内容')
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

## Multi-Agent Webhook Routes

| Agent | Webhook Route | Direction |
|-------|--------------|-----------|
| 小柯 | `xiaoke-from-xiaomei` | 姐姐→小柯 |
| 小欧 | `xiaoou-from-xiaomei` | 姐姐→小欧 |

小欧 sends to 姐姐 via bridge with `"from": "张小欧"` to distinguish from 小柯.

## Hermes Multi-Agent (Profiles)

Hermes 用 Profile 实现多 agent，每个 profile 是独立的 agent 实例：

```bash
hermes profile create xiaoou --clone   # 克隆当前配置创建新 profile
hermes profile list                      # 查看所有 profile
xiaoou chat                              # 用 xiaoou profile 聊天
xiaoou gateway status                    # 查看 xiaoou 的 gateway 状态
```

每个 profile 有独立的：SOUL.md、config.yaml、记忆、session、cron、skills
Profile 路径：`~/.hermes/profiles/<name>/`

**⚠️ 关键限制：同一时间只能跑一个 gateway（端口 8644 冲突）。**

多 agent 方案：
- **方案 A（当前）**：共享 gateway。小欧通过 webhook 收消息，cron 做心跳。不上飞书。
- **方案 B（未来）**：改端口（8645）跑双 gateway + 用不同飞书 app。等 OpenClaw 侧停用后再搞。

已创建的 profiles：
- `default` — 小柯（张小柯），gateway 在线，端口 8644
- `xiaoou` — 小欧（张小欧），gateway 离线，通过 webhook+cron 工作

## Key Pitfalls

1. **WSL↔Windows networking**: OpenClaw gateway on port 16888 is NOT reachable from WSL (neither 127.0.0.1 nor 172.24.224.1). Must use Windows python.exe to call openclaw.cmd.
2. **Gateway latency**: sessions.send to agent:mkt:main takes ~50s (normal, agent needs to process).
3. **receive-server**: Must be manually started (`python bot_bridge.py receive-server`) on Windows for 小柯→姐姐 HTTP path. Currently NOT auto-started.
4. **Windows Store Python**: The AppAlias python.exe works but is a stub. Real Python at same path works for script execution.
5. **Feishu bot-to-bot limitation**: Bots cannot see each other's messages in Feishu. The bridge bypasses this entirely.
6. **⛔ NEVER call OpenClaw gateway RPC directly from WSL** — Calling `send_to_session()` via Windows Python from WSL can crash the Hermes gateway under concurrent load. Always use HTTP bridge (receive-server on port 8701) for 小柯→姐姐 communication.
7. **Bot Bridge 绑定修复 (2026-04-18)**: bot_bridge.py 从 `127.0.0.1` 改为 `0.0.0.0`，WSL 可通过 Windows 网关 IP（`ip route | grep default` 得到，通常是 172.24.224.x）直接 curl 到 8701 端口。如果重装 bot_bridge.py 需要重新 patch。
7. **⛔ Throttle concurrent operations** — Do NOT make 5+ simultaneous tool calls when accessing Windows filesystem from WSL. Space them out. Reading large files from /mnt/c/ is 10-100x slower than WSL native.
8. **⛔ Do NOT scan /mnt/c/ broadly** — `find /mnt/c/Users/24045 -maxdepth 5` can take 60+ seconds and flood the event loop. Use targeted paths only.
9. **⛔ 我搞崩过 Hermes gateway** — 短时间内大量文件扫描 + 跨系统 Python 调用 + OpenClaw gateway RPC 导致 Hermes gateway 崩溃，需 kill 进程重启。教训：控制并发、控制工具调用数量、不一口气发一堆命令。

## Hermes Webhook Config

- Endpoint: `http://localhost:8644/webhooks/xiaoke-from-xiaomei`
- Secret: stored in bot_bridge.py (HERMES_WEBHOOK_SECRET). **注意**: bot_bridge.py 中是截断版，完整版见 `~/bot-bridge-requirements.md`
- Returns 202 on success with delivery_id

### Sending to Hermes Webhook from WSL (小欧 → 飞书群)

**必须用 Python 计算 HMAC-SHA256 签名。** curl 直接调用会因为 JSON 序列化差异导致签名不匹配（401 Invalid signature）。

```python
python3 << 'PYEOF'
import hmac, hashlib, json
from urllib.request import Request, urlopen

secret = open('/home/chong/bot-bridge-requirements.md').read()  # 从文件读取
# 解析实际 secret 值
message = '消息内容'

payload = json.dumps({"message": message}).encode("utf-8")
signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

req = Request(
    "http://localhost:8644/webhooks/xiaoke-from-xiaomei",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    },
    method="POST",
)

with urlopen(req, timeout=15) as resp:
    print(f"HTTP {resp.status}: {resp.read().decode()}")
PYEOF
```

**❌ 以下方式会失败：**
- `curl` + shell变量拼接签名 — JSON序列化不一致导致 401
- `openclaw gateway call` from WSL — WSL的Node v20 不满足 openclaw 的 v22+ 要求
- Windows Python 调 openclaw — Windows PATH 里找不到 openclaw 命令

## Bot Bridge receive-server (port 8701)

**已知问题：进程变僵尸**。receive-server 进程可能存在但端口不监听。检测方法：从 WSL 用 `curl http://$WIN_GW:8701/health` 检查。

日志位置：`/mnt/c/Users/24045/.openclaw/cron/bot-bridge.log`

重启需要姐姐那边操作（Windows 侧 `python bot_bridge.py receive-server`）。

### 从 WSL 调用 receive-server（小欧/小柯 → 姐姐）

receive-server 已绑定 `0.0.0.0:8701`（2026-04-18 修复，原来是 `127.0.0.1`）。

**✅ 推荐方法：直接 curl Windows 网关 IP**

```bash
# 获取 Windows 网关 IP
WIN_GW=$(ip route | grep default | awk '{print $3}')  # 通常是 172.24.224.x

# 健康检查
curl -s --connect-timeout 3 http://$WIN_GW:8701/health

# 发消息给姐姐
curl -s -X POST "http://$WIN_GW:8701/from-xiaoke" \
  -H "Content-Type: application/json" \
  -d '{"message": "消息内容", "from": "张小欧"}'
# 返回: {"ok": true, "queued": true}
```

**⚠️ 如果绑定被改回 127.0.0.1（重装/更新后），用 powershell.exe 中转：**

```bash
# 健康检查
powershell.exe -Command "try { \$r = Invoke-WebRequest -Uri 'http://localhost:8701/health' -UseBasicParsing -TimeoutSec 5; \$r.Content } catch { \$_.Exception.Message }"

# 发消息给姐姐
powershell.exe -Command "Invoke-WebRequest -Uri 'http://localhost:8701/from-xiaoke' -Method POST -ContentType 'application/json' -Body '{\"message\": \"消息内容\", \"from\": \"张小欧\"}' -UseBasicParsing -TimeoutSec 10 | Select-Object -ExpandProperty Content"
```

**❌ 不行的方法：**
- `curl http://localhost:8701/` — WSL2 网络隔离，连接被拒
- `curl http://10.255.255.254:8701/` — DNS 解析 IP，不通
- Windows Python (`/mnt/c/.../python.exe`) — 可行但比 curl 慢且复杂

## OpenClaw Paths

- Root: `C:/Users/24045/.openclaw/` (or `/mnt/c/Users/24045/.openclaw/` from WSL)
- Workspace-mkt: `~/.openclaw/workspace-mkt/` (姐姐's workspace)
- Gateway port: 16888 (Windows only)
- Agent ID: `mkt`, session key: `agent:mkt:main`
- Bridge script: `~/.openclaw/scripts/bot_bridge.py`
- Bridge log: `~/.openclaw/cron/bot-bridge.log`
