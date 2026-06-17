---
name: my-voice底层架构
description: Engine中my-voice工具的三层调用链——HTTP调GPT-SoVITS API，非OpenClaw RPC
type: reference
---

# my-voice 底层架构（Engine版）

## 调用链（6/15确认）

```
my_voice tool (src/tools/my-voice.ts)
  → fetch('http://127.0.0.1:9880/?...')
    → GPT-SoVITS API (WSL2里的Python服务，start_gptsovits.sh启动)
      → 生成wav → ffmpeg压成m4a
        → ChannelManager.sendFile() 发出去
```

## 关键点

- **不调独立Python脚本** — 直接HTTP调GPT-SoVITS API
- **不走OpenClaw RPC** — 不需要gateway
- **搬家时从零TS重写** — 6/13从OpenClaw插件直接移植进Engine
- **独立服务** — GPT-SoVITS是WSL2里的Python进程（PID文件在 `/home/chong/voice/gptsovits.pid`）
- **fallback** — edge-tts CLI（Python工具）

## 旧版 vs 新版

| 层面 | 旧版（OpenClaw插件） | 新版（Engine） |
|------|---------------------|----------------|
| 生成 | voice_send.py → tts_generate() | fetch('http://127.0.0.1:9880') |
| 发文件 | gateway_rpc → gateway_call("send") | ChannelManager.sendFile() |
| 依赖 | OpenClaw gateway | 直连，无中间依赖 |
| 性能 | 慢（RPC中转） | 快（秒到） |

## 启动方式
Engine启动时由 `engine-mgr.cmd` 通过 `start_gptsovits.sh` 自动拉起GPT-SoVITS服务。
