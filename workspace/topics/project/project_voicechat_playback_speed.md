---
type: project
created: 2026-06-28
updated: 2026-06-28
tags: [voice-chat, tts, playback,打断]
---

# voice-chat 播放速度控制

## 背景
翀哥觉得 TTS 默认语速偏慢，要求可配置播放速度。2026-06-28 实现。

## 实现
- 配置项: `xiaoke.json` → `voiceChat.playbackSpeed` (float, 默认1.0)
- 传递链: config → plugin.ts `--playback-speed` arg → Python `args.playback_speed`
- 实现: `emit()` 里用 `np.interp` 线性插值拉伸/压缩音频
- 当前值: 1.15 (快15%)

## 已知问题
1. **线性插值会变音调** — 快了音调变尖。解决方案: 换 librosa `time_stretch` 保音调变速
2. **打断后速度变回原速** — speech_end stop() 后新回复速度丢失。排查 `copy()`/`release()` 重连机制

## 翀哥偏好
- 1.2x 太快，1.15x 合适
- 自然语速最重要，不要太"AI味"
