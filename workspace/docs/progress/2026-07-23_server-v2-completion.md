# 2026-07-23 server_v2 完善日

## 今日完成

### 1. 语音打断链路打通（下午）
- SSH 全局单例 + 作用域 bug 修复（`_ssh_exec` 缺 `nonlocal _ssh_client`）
- `ssh_curl_post` 注入给 interrupt（之前从未注入 = None）
- 打断链路全通：VAD speech_end → interrupt → 清队列 + SSH stop 235

### 2. voice-chat 跳过 stop-hook
- sessionId.includes('voice-chat') 直接跳过，不再浪费 LLM judge 调用

### 3. 页面状态修复
- Pull 状态：用 `_has_data` 代替 `_started`（收到数据才显示运行中）
- 延迟面板：engine_latency + timing_235 + tts_latency + frames + A-V pts diff

### 4. Ctrl+C 优雅退出
- exception handler 静默 ConnectionResetError

### 5. Perception 搬到 server_v2
- perception_adapter.py（薄封装 PerceptionManager）
- VideoReceiver 接收摄像头帧 → 喂 perception
- 摄像头上行 + 小窗显示（getUserMedia video: true）
- uplink POST engine 附带最近 5 条画面描述

### 6. avatar=none 本地 TTS
- LocalTTSAudioTrack（PCM float32 → AudioFrame → Opus）
- voice_reply 分流（local=本地TTS / autodl=SSH 235）
- config.json + config-autodl.json + --profile 支持
- .env 支持（DASHSCOPE_API_KEY）

### 7. 本地 TTS 吞音修复
- **根因：UnboundLocalError(result)** — voice_reply avatar=none 分支没定义 result 变量 → 500 报错
- realtime 节奏控制（wall-clock + pts + sleep）—— aiortc 完全靠 recv() 里 sleep
- reset() API + voice_reply 触发 TTS 前重置基准

### 8. mode 判断重构
- `avatar_provider == "none"` → `config.is_local`（显式 mode 字段）
- config.json 加 `"mode": "local"` / config-autodl.json 加 `"mode": "autodl"`
- 兼容：无 mode 字段时从 avatar_provider 推断

## 关键 commit
- `f8c53bef` SSH 作用域 bug
- `49f37156` ssh_curl_post 注入
- `03320f58` voice-chat 跳过 stop-hook
- `f5490100` Perception 搬到 server_v2
- `a265701f` 摄像头上行 + 小窗
- `cf5da29d` avatar=none 本地 TTS
- `eafd0e14` 加回 sleep + SSH 修复
- `316d36fe` mode 判断重构

## 教训
- **写新东西先设计框架，别边写边堆**（server.py 一锅粥导致 server_v2 从头来）
- **debug 要看 log 不要猜**（吞音猜了好几版 sleep，根因是 UnboundLocalError）
- **config 两套不能来回改**（autodl 调好本地又不行 = 教训）
- aiortc 完全靠 recv() 里 sleep 控制 pacing，pts 不参与发送节拍

## 明天待办
- 首字吞字微调
- #91 blocked 任务自动追踪（15:00）
- 翀哥肠镜（早上 8:00）
- 换 TTS + 热加载 avatar（需要设计）
