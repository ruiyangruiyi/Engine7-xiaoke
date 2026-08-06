# voice-chat 模块目录结构设计

> 日期：2026-06-26 | 作者：小柯 | 状态：待翀哥确认

## 命名

**`src/voice-chat/`**

理由：
- 直白——语音聊天管线，一看就懂
- 跟现有 `channels/`（文本通道）、`inner-voice/`（内心独白）平行
- 不叫 `oac`——这是我们自己的，只是借鉴了 OAC 的管线设计
- 不叫 `voice`——跟现有 TTS tool 的 feature id 冲突

备选：`realtime`（实时通信）、`avatar-chat`（数字人聊天）

---

## 目录结构

```
src/voice-chat/
├── types.ts                     # 类型定义
├── config.ts                    # 配置解析（voiceChat 配置段）
├── plugin.ts                    # 引擎插件入口（启动/停止 Python 服务 + 注册 bridge）
├── bridge.ts                    # engine ↔ Python HTTP 通信（从 integrations/oac-bridge.ts 迁入）
├── README.md                    # 模块说明
│
├── python/                      # Python 语音管线（engine 管理的子进程）
│   ├── server.py                # 主入口：fastrtc WebRTC + 管线编排 + HTTP API
│   ├── vad.py                   # Silero VAD 状态机（~100行）
│   ├── asr.py                   # SenseVoice ASR 封装（~30行，含 language="zh"）
│   ├── tts.py                   # 百炼 CosyVoice TTS 封装（~30行）
│   ├── requirements.txt         # onnxruntime / funasr / torch / fastrtc / numpy
│   └── README.md                # Python 运行说明（模型下载、依赖安装）
```

---

## 各文件职责

### TypeScript 侧（engine 集成层）

| 文件 | 职责 | 行数估算 |
|------|------|----------|
| `types.ts` | VoiceChatConfig、VoiceChatStatus 等类型 | ~30 |
| `config.ts` | 从 engine config 解析 voiceChat 配置段 | ~40 |
| `plugin.ts` | 类似 InnerVoicePlugin：启动时 spawn Python 子进程，停止时 kill；注册 bridge webhook | ~100 |
| `bridge.ts` | 从现有 `integrations/oac-bridge.ts` 迁入，改名适配 | ~100（现有代码微调） |

### Python 侧（音频处理管线）

| 文件 | 职责 | 来源 |
|------|------|------|
| `server.py` | fastrtc WebRTC endpoint + VAD→ASR→POST engine + 接收 engine 回复→TTS→回传浏览器 | 新写，~200行 |
| `vad.py` | Silero VAD ONNX 推理 + 4 状态机 | 从调研文档第6节最小管线抠出 |
| `asr.py` | funasr SenseVoice 封装，构造时 language="zh" | 从调研文档抠出 |
| `tts.py` | 百炼 CosyVoice API 调用 | 从 OAC tts_handler_cosyvoice_bailian.py 精简 |

---

## 数据流

```
浏览器 ──WebRTC──→ python/server.py
                      │
                      ▼
                   vad.py (Silero ONNX)
                      │ 语音段
                      ▼
                   asr.py (SenseVoice, language="zh")
                      │ 中文文字
                      ▼
                   POST → engine /webhook/voice-chat
                      │
                   engine 处理（LLM + 记忆 + 工具）
                      │
                   回复 ← POST /voice-reply
                      │
                      ▼
                   tts.py (百炼 CosyVoice)
                      │ 音频 24kHz
                      ▼
                   回传浏览器 ← WebRTC emit
```

---

## 跟现有代码的关系

1. **`integrations/oac-bridge.ts`** → 迁入 `bridge.ts`，endpoint 从 `/webhook/oac-bridge` 改为 `/webhook/voice-chat`
2. **`integrations/cognifold-*.ts`** → 不动，CogniFold 是独立集成
3. **engine-startup.ts** → 原来调 `registerOacBridge()` 的地方改为 `VoiceChatPlugin.start()`
4. **配置** → config.json 新增 `voiceChat` 配置段（取代 `oacBridge`）

---

## 不放进去的

- **模型文件**（silero_vad.onnx、SenseVoiceSmall）→ 太大，放 python/models/ 但 gitignore
- **Avatar 渲染**（LiteAvatar/FlashHead）→ 后续单独模块，先把语音管线跑通
- **OAC 框架代码**（DataSink/StreamManager/HandlerBase）→ 不要，我们用自己的 HTTP 通信
