# Decision 2026-07-10 — voice-chat 模式切换（v1 + v2 兼容）

## 背景

父 7/10 08:43 指令：
> v1 的本地 tts 语音方案是一种模式，应该留着，这作用于不用开 autodl 就可以实现语音实时交互。server 可以根据需要实时用命令或者配置切换后面。需要兼容。

## 现状

- **v1（local 模式）**：mic → Silero VAD → ASR → engine → 本地 TTS（edge-tts / GPT-SoVITS） → 浏览器（PyAV 编码）
  - 优点：不依赖 autodl，本机就能跑，调试方便
  - 场景：开发、单机 demo、低延迟对话
- **v2（bypass 模式）**：Carpo SDK pull → PyAV Opus decode → 浏览器
  - 优点：流式、低延迟、走真物理通道
  - 场景：autodl 235/268 推流时（FlashHead avatar + CosyVoice TTS）

## 决策

**两种模式并存**，server 启动时+运行时都能切换。

### 切换方式（三选一）

1. **启动时**：`--mode local|bypass|auto`
2. **运行时 API**：`POST /mode {mode: "local|bypass|auto"}`
3. **配置文件**：`machines.json` 或新建 `voicechat_config.json` 加 `mode` 字段

### Auto 模式行为

- 检查 autodl 235 是否可达（`curl http://localhost:8899/health`）
- 可达 → bypass
- 不可达 → local（降级）

### 代码改动

1. `server.py` 增加：
   ```python
   VOICECHAT_MODE = os.environ.get("VOICECHAT_MODE", "auto")  # local|bypass|auto

   # 启动时根据模式决定:
   if mode == "local":
       # 注册 mic→VAD→ASR→TTS 路径（v1）
   elif mode == "bypass":
       # 注册 carpo pull→PyAV decode 路径（v2）
   elif mode == "auto":
       # 探测 autodl health，动态选
   ```
2. 启动后 `/mode` endpoint 动态切换（**热切换**：关闭旧路径、注册新路径）
3. 删除 / 注释 `BYPASS_VAD_ASR` 这个环境变量开关（被 mode 取代）

## 待父确认

1. 配置文件用 `machines.json` 还是新建 `voicechat_config.json`？
2. 切换时浏览器要不要重连 WebRTC？
3. auto 模式探测阈值（health 失败几次降级）？

## 不做的事

- 不删 v1 代码（父明确要保留）
- 不把 mode 写死在 server.py
- 不破坏现有 v2 链路（已通）