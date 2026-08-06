# voice-chat TTS/Avatar 可插拔管线 Spec

**日期：** 2026-06-28
**参与者：** 翀哥确认方案，小柯实施

## 背景

voice-chat 上行已通（浏览器→VAD→ASR→engine），下行未通（engine回复→TTS→浏览器听不到声音）。

需要：TTS 和 Avatar 可插拔，配置选 provider，随时能换。

## 管线结构

```
engine 回复文字
      │
      ▼
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ TTSProvider │────▶│ AvatarProvider  │────▶│ WebRTC emit()    │──▶ 浏览器
│ (音频合成)  │     │ (视频/纯音频)   │     │ (音频/视频推流)  │
└─────────────┘     └─────────────────┘     └──────────────────┘
```

每个节点可独立替换，互不依赖。

## 接口定义

### TTSProvider

```python
# python/tts/base.py
class TTSProvider:
    """TTS 统一接口"""
    def synthesize(self, text: str) -> np.ndarray:
        """
        文字 → 音频
        Returns: float32, 24kHz, mono
        """
        raise NotImplementedError
```

### AvatarProvider

```python
# python/avatar/base.py
class AvatarProvider:
    """Avatar 统一接口"""
    def render(self, audio: np.ndarray, text: str) -> tuple[np.ndarray | None, np.ndarray]:
        """
        音频 → 视频+音频
        Returns: (视频帧数组 | None, 音频)
                 None = 纯音频模式（WebRTC 只推音频）
        """
        raise NotImplementedError
```

## Provider 实现

### TTS Providers

| Provider | 文件 | 说明 | 依赖 |
|----------|------|------|------|
| cosyvoice | `tts/cosyvoice.py` | 百炼 CosyVoice API（从当前 tts.py 迁入） | dashscope SDK + API Key |
| edgetts | `tts/edgetts.py`（Phase 2） | 微软 Edge TTS，免费快 | edge-tts pip 包 |

### Avatar Providers

| Provider | 文件 | 说明 |
|----------|------|------|
| none | `avatar/none.py` | passthrough，只返回音频（默认） |
| flashhead | `avatar/flashhead.py`（Phase 3） | 云端 API 调用 FlashHead |

## 配置（xiaoke.json voiceChat 段）

```json
{
  "voiceChat": {
    "enabled": true,
    "model": "deepseek/deepseek-v4-flash",
    "thinking": false,
    "tts": {
      "provider": "cosyvoice",
      "apiKey": "sk-xxx",
      "voice": "",
      "model": "cosyvoice-1"
    },
    "avatar": {
      "provider": "none"
    }
  }
}
```

- `tts.provider` 不配或空 → 不出声（engine 回复 POST 回 Python 后丢弃）
- `tts.provider` 配了但 apiKey 缺 → 启动时报错
- `avatar.provider` 不配或 "none" → 纯音频模式

## Python 目录结构（改动后）

```
python/
├── server.py          # 主服务（管线编排）
├── tts/
│   ├── __init__.py    # 工厂函数 create_tts(config) → TTSProvider
│   ├── base.py        # TTSProvider 接口
│   └── cosyvoice.py   # 百炼 CosyVoice 实现
├── avatar/
│   ├── __init__.py    # 工厂函数 create_avatar(config) → AvatarProvider
│   ├── base.py        # AvatarProvider 接口
│   └── none.py        # passthrough 实现
├── vad.py             # 不动
├── asr.py             # 不动
├── models/            # 不动
└── requirements.txt   # 不动
```

## TS 侧改动

### types.ts / config.ts

voiceChat 配置段加 `tts` 和 `avatar` 子对象：

```ts
// types.ts
tts?: {
  provider: string
  apiKey?: string
  voice?: string
  model?: string
}
avatar?: {
  provider: string
}
```

### plugin.ts

`startPython()` 里把 tts/avatar 配置作为命令行参数传给 Python：

```python
--tts-provider cosyvoice --tts-api-key sk-xxx --tts-voice "" --tts-model cosyvoice-1
--avatar-provider none
```

### bridge.ts

不动。bridge 只管 engine ↔ Python 的文字通信，TTS/Avatar 全在 Python 侧。

## server.py 改动

### 启动时：创建 provider 实例

```python
# 工厂函数
from tts import create_tts
from avatar import create_avatar

tts = create_tts(args.tts_provider, api_key=args.tts_api_key, ...)
avatar = create_avatar(args.avatar_provider)
```

### receive_tts_audio()：管线编排

```python
async def receive_tts_audio(self, text: str):
    if not tts or not text:
        return
    # Step 1: TTS 合成
    audio = await loop.run_in_executor(None, tts.synthesize, text)
    if len(audio) == 0:
        return
    # Step 2: Avatar 渲染（none = 直接用音频）
    video, audio = await loop.run_in_executor(None, avatar.render, audio, text)
    # Step 3: 推入 WebRTC 队列
    # （MVP: 纯音频，直接推 audio 队列）
    for i in range(0, len(audio) - 480, 480):
        await self._audio_queue.put(audio[i:i + 480])
```

## 实施顺序

1. **tts/ 模块**：base.py（接口）+ cosyvoice.py（从 tts.py 迁入）+ \_\_init\_\_.py（工厂）
2. **avatar/ 模块**：base.py（接口）+ none.py（passthrough）+ \_\_init\_\_.py（工厂）
3. **server.py**：import 新模块，改 receive_tts_audio() 走管线
4. **TS 侧**：types.ts + config.ts 加配置，plugin.ts 传参
5. **xiaoke.json**：配 tts.apiKey + provider
6. **删除旧 tts.py**

## 验证标准

1. 浏览器开 voice-chat 页面，说话后能听到 TTS 回复声音
2. 配 `tts.provider: "cosyvoice"` 有声音，改成不配 → 没声音（不出错）
3. 日志显示 `[tts] Synthesis complete` + `[server] TTS audio queued: N chunks`
4. `avatar.provider: "none"` 时 WebRTC 只有音频轨

## 不做

- 流式 TTS（当前是 synthesize 一次性合成，后面再优化）
- EOU 语义切分（Phase 3，已记在文档）
- FlashHead Avatar（Phase 3）
- 热插拔 provider（配置级够了）
