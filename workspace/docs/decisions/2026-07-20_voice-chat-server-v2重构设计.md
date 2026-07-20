# 2026-07-20 Voice-Chat server_v2 重构设计

## 目标

用 aiortc 全 passthrough 替代 fastrtc，模块化设计便于扩展。

## 原则

1. **新文件 server_v2.py**，保留 server.py / carpo_rtc_server.py 不动
2. **不动 autodl 端**（235 的 FlashHead / carpo_avatar_server）
3. **模块化**——每个模块独立文件，server_v2.py 只负责拼起来
4. **复用 demo_v4 验证过的 Carpo pull + NAL 攒包 + force_codec 逻辑**

## 模块划分

```
engine/src/voice-chat/python/
├── server.py              ← v1 入口（保留，1756行，不动）
├── carpo_rtc_server.py    ← fastrtc 版（保留，不动）
├── server_v2.py           ← 新入口（<100行，只拼装）
├── aiortc_demo_v4.py      ← demo（保留，参考用）
│
├── v2/                    ← 新模块目录
│   ├── __init__.py
│   ├── config.py          配置（端口、模型、235地址、SSRC等）
│   ├── carpo_pull.py      Carpo SDK pull + NAL 攒包（从 demo_v4 提取）
│   ├── rtc.py             aiortc WebRTC 层（offer/answer, tracks, force_codec）
│   ├── audio_up.py        上行链路（mic → VAD → ASR → engine）
│   ├── tts_down.py        下行链路（engine → TTS → 235 FlashHead → Carpo push）
│   ├── interrupt.py       打断逻辑
│   └── web/               前端
│       ├── index.html     主页面（settings + video + PiP + 延迟面板）
│       └── app.js         前端逻辑（RTCPeerConnection + generate + 打断）
```

## 模块接口

### config.py
```python
@dataclass
class Config:
    # WebRTC
    rtc_port: int = 8120
    # Carpo pull
    carpo_server: str = "192.144.156.158:23800"
    carpo_remote_ip: str = "106.39.200.204"
    ssrc_local_audio: int = 99999
    ssrc_local_video: int = 11111
    ssrc_remote_audio: int = 12345
    ssrc_remote_video: int = 67890
    # PTS
    pts_mode: str = "fixed"  # fixed | sdk
    # TTS / FlashHead
    flashhead_url: str = "http://..."
    tts_provider: str = "cosyvoice"
    # VAD / ASR
    vad_threshold: float = 0.5
    asr_model: str = "..."
```

### carpo_pull.py
```python
class CarpoPuller:
    """Carpo SDK pull + NAL 攒包，从 demo_v4 提取"""
    def __init__(self, config: Config)
    def start(self, audio_queue: asyncio.Queue, video_queue: asyncio.Queue)
    def stop(self)
```

### rtc.py
```python
class WebRTCHandler:
    """aiortc offer/answer + tracks + force_codec"""
    def __init__(self, config: Config, audio_queue, video_queue)
    async def handle_offer(self, sdp, type) -> dict  # 返回 answer
```

### audio_up.py
```python
class AudioUpstream:
    """mic → VAD → ASR → engine"""
    def __init__(self, config: Config)
    async def handle_mic_data(self, pcm: bytes) -> str | None  # 返回 ASR 文本
```

### tts_down.py
```python
class TTSDownstream:
    """engine → TTS → 235 FlashHead → Carpo push"""
    def __init__(self, config: Config)
    async def send_text(self, text: str)  # 触发 235 生成
```

### interrupt.py
```python
class InterruptManager:
    """打断逻辑：检测用户说话 → 停止 TTS + FlashHead"""
    def __init__(self, config: Config)
    async def check_and_interrupt(self, pcm: bytes) -> bool
```

### server_v2.py（入口）
```python
#!/usr/bin/env python
"""server_v2.py — 模块化 voice-chat server（aiortc 全 passthrough）"""
from v2.config import Config
from v2.carpo_pull import CarpoPuller
from v2.rtc import WebRTCHandler
from v2.audio_up import AudioUpstream
from v2.tts_down import TTSDownstream
from v2.interrupt import InterruptManager
from aiohttp import web

async def main():
    config = Config()
    audio_queue = asyncio.Queue()
    video_queue = asyncio.Queue()
    
    carpo = CarpoPuller(config)
    carpo.start(audio_queue, video_queue)
    
    rtc = WebRTCHandler(config, audio_queue, video_queue)
    audio_up = AudioUpstream(config)
    tts_down = TTSDownstream(config)
    interrupt = InterruptManager(config)
    
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text=INDEX_HTML, content_type='text/html'))
    app.router.add_post('/offer', rtc.handle_offer)
    app.router.add_post('/generate', tts_down.handle_generate)
    web.run_app(app, port=config.rtc_port)
```

## API 设计

| 路径 | 方法 | 用途 |
|------|------|------|
| `/` | GET | 前端页面 |
| `/offer` | POST | WebRTC 握手（aiortc answer） |
| `/generate` | POST | 触发 235 FlashHead 生成（文字 → 音频+视频） |
| `/api/settings` | GET/POST | 配置（TTS provider、形象等） |
| `/api/avatar/switch` | POST | 形象热切换 |
| `/health` | GET | 健康检查 |

## 前端设计

从 server.py 提取，保留：
- Settings modal（TTS provider、形象选择）
- Video 窗口（PiP 支持）
- 延迟面板（各环节 timing）
- 打断按钮 + 自动打断

改动：
- WebRTC 握手从 fastrtc Stream → 标准 RTCPeerConnection
- 新增 video track 显示

## 实施步骤

### Phase 1：架子 + Carpo pull + WebRTC（半天）
1. 创建 v2/ 目录结构
2. 从 demo_v4 提取 carpo_pull.py + rtc.py
3. server_v2.py 跑起来，浏览器能看到画面+声音
4. **验证**：跟 demo_v4 一样的效果

### Phase 2：上行链路（半天）
1. 从 server.py 提取 VAD → ASR → engine
2. 前端加 mic 上行
3. **验证**：说话能触发 ASR → engine 回复

### Phase 3：TTS 下行 + 打断（半天）
1. 从 carpo_rtc_server.py 提取 TTS → 235 FlashHead
2. 从 server.py 提取打断逻辑
3. **验证**：完整对话流程 + 打断

### Phase 4：前端完善（半天）
1. Settings 页迁移
2. 延迟面板
3. 形象热切换
4. **验证**：所有功能完整

## 风险

1. **VAD/ASR 提取**：server.py 1756 行耦合较深，提取时注意依赖
2. **打断逻辑**：需要跟 235 FlashHead 联动，涉及 autodl 端 API（不改，只是调）
3. **前端重写**：WebRTC 握手变了，前端 JS 要大改

## 不做的事

- 不改 autodl 端（235 FlashHead / carpo_avatar_server）
- 不删 server.py / carpo_rtc_server.py
- 不做新功能（只迁移现有功能到模块化结构）
