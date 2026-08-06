# SOP: 同步 Python 代码到 AutoDL 268

> 2026-07-09 小柯补（翀哥指出"本地目录没记"+ 让我去 git 上找）
> ⚠️ **第一次版本写错了——本地不是 autodlv2/python/oac/，是 voice-chat-python/autodl/**

## 真相

**本地 git repo**：`D:/work/code/LovePea/`（master 分支，origin: github.com/ruiyangruiyi/LovePea.git）

## 工作目录（已统一）

| 目录 | 用途 |
|------|------|
| `engine/src/voice-chat/python/` | **唯一 runtime 目录**：server.py、handler、carpo_pull_server.py |
| `voice-chat-python/autodl/` | **268 部署源码**（git 管理，sync 源） |

```
voice-chat-python/autodl/          ← 同步到 /root/carpo_sdk/
├── carpo.py                       ← ctypes bindings (7/4)
├── carpo_avatar_server.py         ← HTTP POST /generate + WS /ws/generate (7/8)
├── carpo_oac_bridge.py            ← FlashHead → Carpo push 桥 (7/8)
├── flashhead_processor.py         ← 主 processor (7/7)
├── start_carpo_avatar.sh          ← 启动脚本 (7/7)
└── start_oac.sh
```

**268 部署目录**：`/root/carpo_sdk/`（通过 sftp 同步过去）
```
/root/carpo_sdk/
├── carpo.py                      ← 从本地推
├── carpo_avatar_server.py        ← 从本地推
├── carpo_oac_bridge.py           ← 从本地推
├── flashhead_processor.py        ← 从本地推
├── libcarpo.so                   ← Linux 编译产物（不来自本地，本地是 Win DLL）
├── libcarpo_089.so               ← 历史
├── libcarpo_268.so.bak           ← 历史
├── cross_machine_e2e.py          ← 测试
├── test_*.py                     ← 测试脚本
├── cpu_info_stub.c               ← 测试 stub
└── flash_head/ → /root/OpenAvatarChat/src/handlers/avatar/flashhead/SoulX-FlashHead/flash_head
```

**268 启动脚本**：`/root/start_carpo_avatar.sh`（也来自 voice-chat-python/autodl/）

## 同步步骤

### 1. 改本地源码
```bash
$EDITOR D:/work/code/LovePea/voice-chat-python/autodl/carpo_avatar_server.py
```

### 2. sftp 推送到 268

```python
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("connect.bjb1.seetacloud.com", port=40458, username="root", password="NIgDNE+SPYSM",
            disabled_algorithms={"pubkeys": ["rsa-sha2-256","rsa-sha2-512"]}, timeout=15)
sftp = ssh.open_sftp()

# 同步所有需要的文件
files = [
    "carpo.py",
    "carpo_avatar_server.py",
    "carpo_oac_bridge.py",
    "flashhead_processor.py",
    "start_carpo_avatar.sh",
]
LOCAL_DIR = r"D:\work\code\LovePea\voice-chat-python\autodl"
REMOTE_DIR = "/root/carpo_sdk"
for f in files:
    sftp.put(f"{LOCAL_DIR}/{f}", f"{REMOTE_DIR}/{f}")
    print(f"pushed: {f}")

sftp.close(); ssh.close()
```

### 3. 重启 268 服务

```bash
ssh -p 40458 root@connect.bjb1.seetacloud.com

# 停服务
pkill -f carpo_avatar_server.py

# 启动
nohup bash /root/start_carpo_avatar.sh > /tmp/avatar.log 2>&1 &

# 等 30 秒让 FlashHead pipeline 加载
sleep 30

# 验证
curl -s http://localhost:8899/health
# 期望: {"status":"ok","models_loaded":true}
```

### 4. 本机 git 提交

```bash
cd D:/work/code/LovePea
git add voice-chat-python/autodl/
git commit -m "feat: xxx"
git push origin master
```

## ⚠️ 不要做的事

1. **不要在 268 上直接 `vim`** — 改完忘了本地，本地/268 不一致，下次又对不上
2. **不要往 /root/carpo_sdk/ 推新脚本不通知** — 父会看不到，且污染环境（`_loop_tts_demo.py` 教训）
3. **不要忘了 LovePea 是 git repo** — 所有改动要 commit + push
4. **不要把 voice-chat-python/autodl/ 和 autodlv2/python/oac/ 搞混** — 前者是真本地，后者是之前混淆的

## 268 文件变更记录

| 时间 | 文件 | 操作 |
|------|------|------|
| 7/4 08:19 | carpo.py | 推 |
| 7/4 08:19 | carpo_bridge.py (旧) | 推 |
| 7/7 22:18 | flashhead_processor.py | 推 |
| 7/8 10:56 | carpo_oac_bridge.py | 推 |
| 7/8 10:59 | carpo_avatar_server.py | 推 |
| 7/9 08:23 | _loop_tts_demo.py | **小柯推的污染，父决定删不删** |