# server_v2 avatar=none 本地 TTS 方案

## 核心挑战

**格式不匹配**：
- CarpoAudioTrack 吃 `(opus_bytes, ts_ms)` — Opus passthrough
- CosyVoice TTS 产出 PCM float32 24kHz，每 480 samples（20ms）一个 chunk
- aiortc 的 Opus encoder 吃 `av.AudioFrame`（PCM），自动编码 Opus

**解法**：新建 `LocalTTSAudioTrack`，吃 PCM queue → 包成 `av.AudioFrame` → aiortc 自动编码 Opus。

## 改动清单

1. config.py — 加 avatar_provider/tts_provider/tts_* 字段 + 读 config.json
2. rtc.py — 新增 LocalTTSAudioTrack（PCM→AudioFrame→Opus）
3. rtc.py — WebRTCHandler 按 avatar_provider 选 track
4. server_v2.py — voice_reply 分流（none=本地TTS / autodl=SSH 235）
5. server_v2.py — on_startup 按 mode 初始化（none=创建TTS / autodl=Carpo pull）
6. 前端 avatar=none 时不显示 video（已有逻辑 ✅）

## 不做
- 运行时热切换 avatar_provider（重启才行）
- GPT-SoVITS / EdgeTTS
- 视频轨（avatar=none 无视频）
