# Voice-Chat 换机部署流程

> 2026-07-14 小柯整理
> 教训：268 不是完整 clone，手动补文件花了半小时，还漏了 libcarpo.so

## 前提

- 目标机器是 AutoDL RTX 4090，已装好 conda 环境（flashhead）
- SoulX-FlashHead 和 carpo_sdk 目录已存在（如果不是，需要先 clone 或上传）

## 部署清单（5 步）

### 1. 同步代码

从本地上传以下文件到目标机器：

```python
# 本地路径 → 远程路径
files = {
    # 核心 server
    "engine/src/voice-chat/autodlv2/python/oac/carpo_avatar_server.py": "/root/carpo_sdk/carpo_avatar_server.py",
    "engine/src/voice-chat/autodlv2/python/oac/avatar_handler_flashhead.py": "/root/carpo_sdk/avatar_handler_flashhead.py",
    "engine/src/voice-chat/autodlv2/python/oac/flashhead_processor.py": "/root/carpo_sdk/flashhead_processor.py",
    "engine/src/voice-chat/autodlv2/python/oac/carpo_oac_bridge.py": "/root/carpo_sdk/carpo_oac_bridge.py",
    # TTS
    "engine/src/voice-chat/autodlv2/python/tts/gptsovits.py": "/root/carpo_sdk/tts/gptsovits.py",
    "engine/src/voice-chat/autodlv2/python/tts/local_cosyvoice2.py": "/root/carpo_sdk/tts/local_cosyvoice2.py",
    "engine/src/voice-chat/autodlv2/python/tts/dashscope_cosyvoice.py": "/root/carpo_sdk/tts/dashscope_cosyvoice.py",
    "engine/src/voice-chat/autodlv2/python/tts/base.py": "/root/carpo_sdk/tts/base.py",
}
```

### 2. 检查 libcarpo.so

**必须用能跑的版本**（md5: `2deea3f9f6be7127fcff17f35fc1ea52`，2107824 bytes）

```bash
# 检查目标机器
md5sum /root/carpo_sdk/libcarpo.so

# 如果不对，从本地上传
# 本地路径: engine/src/voice-chat/autodlv2/libcarpo/libcarpo_235.so
# 上传到: /root/carpo_sdk/libcarpo.so
```

**常见错误**：`OSError: libcarpo.so: undefined symbol: WebRtc_GetCPUInfo` → libcarpo.so 版本不对

### 3. 检查启动脚本

```bash
cat /root/start_carpo_avatar.sh
```

确认以下变量正确：
- `PYTHONPATH` 包含 OpenAvatarChat handlers + SoulX-FlashHead + carpo_sdk
- `DASHSCOPE_API_KEY` 已设置
- `CARPO_SERVER=192.144.156.158`
- `CARPO_PORT=23800`
- `LD_LIBRARY_PATH` 包含 carpo_sdk
- Python 路径正确（通常是 `/root/autodl-tmp/envs/flashhead/bin/python`）

### 4. 改 machines.json

本地 `engine/src/voice-chat/machines.json`：
```json
{
  "active": "bjXXX",  // 改成目标机器 ID
  "machines": {
    "bjXXX": {
      "host": "connect.bjb1.seetacloud.com",
      "port": XXXXX,  // SSH 端口
      "user": "root",
      "password": "XXXXX",
      ...
    }
  }
}
```

### 5. 改 server.py machine 设置

```bash
# 通过 API 改（不重启）
curl -sk -X POST https://127.0.0.1:8011/api/settings \
  -H "Content-Type: application/json" \
  -d '{"machine":"bjXXX","avatar_provider":"autodl","tts_provider":"none"}'
```

然后重启 voice-chat server。

## 验证

```bash
# 1. 检查服务状态
python avatarctl.py status

# 2. 检查 /generate 返回 timing
python3 -c "
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('host', port=XXXX, username='root', password='XXXX')
si,so,se = ssh.exec_command('curl -s http://localhost:8899/health')
print(so.read().decode())
ssh.close()
"

# 3. 浏览器测：说一句话，看嘴型动+延迟面板亮
```

## avatarctl.py 用法

```bash
cd engine/src/voice-chat/autodlv2
python avatarctl.py start    # 启动
python avatarctl.py stop     # 停止
python avatarctl.py status   # 状态（含 GPU/health/avatar）
python avatarctl.py restart  # 重启
```

## 已知坑

| 坑 | 症状 | 解法 |
|----|------|------|
| libcarpo.so 版本不对 | `undefined symbol: WebRtc_GetCPUInfo` | 传 libcarpo_235.so |
| avatar_handler_flashhead.py 缺失 | ImportError | 上传到 /root/carpo_sdk/ |
| machine 指向旧机器 | trigger 发错地方，嘴型不动 | API 改 machine 或改 config.json |
| config.json 凭据被覆盖 | 切模式后 TTS 没声音 | 凭据只从 args 读，不进 config.json |
| SSH nohup 超时 | avatarctl start 报 timeout | 不影响，服务已在后台启动，等 30s 后查 status |
