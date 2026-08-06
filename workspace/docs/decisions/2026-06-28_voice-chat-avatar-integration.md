---
type: project
created: 2026-06-28
updated: 2026-06-28
tags: [voice-chat, avatar, flashhead, autodl, tts]
---

# voice-chat Avatar 集成方案（6/28 定稿）

## 背景
6/28 晚翀哥定方向：voice-chat 接 avatar，本机 3060 跑不了 FlashHead，走 AutoDL 4090。

## 双模式设计（翀哥定）

```
模式1：纯语音（当前 voice-chat，低延迟）
  ASR → Engine → 本机 CosyVoice TTS → WebRTC → 浏览器听声音
  不出脸，延迟 ~2-4s

模式2：语音 + 视频（想看人走 AutoDL）
  ASR → Engine → 回复文本
    ├→ 本机 CosyVoice → WebRTC → 浏览器听声音（快）
    └→ SSH → AutoDL /generate → TTS → FlashHead → RTMP → 浏览器看脸（慢几秒）
  声音先到，视频慢但能看到嘴型
```

## TTS 可切换（AutoDL 侧）
- `gptsovits`（本地, :9880）— 现有，姐姐直播用的
- `cosyvoice`（百炼 API）— 新增，跟本机同一个 key
- `/generate` 接口加 `tts_provider` 参数，tts_config.json 加 provider 字段

## 视频回传方案（两阶段）
- **阶段1（先跑通）**: RTMP → 北京 SRS → 浏览器 flv.js 播 HTTP-FLV
  - 复用现有代码，稳定
  - 延迟 1-2s
- **阶段2（后优化）**: SRS 6.0 RTMP→WebRTC 转发
  - 浏览器从 SRS 拉 WebRTC
  - 延迟更低
- **不用 P2P WebRTC** — 本机没公网 IP，打不通

## 可复用代码
- `skills/my-livestream/livestream_send.py` — SSH→AutoDL 全流程（paramiko）
- `livestream/autodl/livestream_server.py` — AutoDL 推理服务
- `livestream/README.md` — 完整管线文档

## 现有 AutoDL 环境
- SSH: connect.bjb1.seetacloud.com:25859, root
- GPT-SoVITS: /root/autodl-tmp/GPT-SoVITS (venv: /root/autodl-tmp/envs/gptsovits)
- FlashHead: /root/SoulX-FlashHead (ckpt: SoulX-FlashHead-1_3B)
- RTMP: rtmp://192.144.156.158:1935/live/stream (北京SRS 6.0)
- HTTP-FLV: http://192.144.156.158:8080/live/stream.flv
- 参考: 06.jpg (默认avatar形象)

## 明天改动清单
1. `livestream_server.py` `/generate` 加 `tts_provider` 参数（cosyvoice 选项）
2. voice-chat bridge: engine 回复时可选触发 AutoDL `/generate`（配置开关）
3. 浏览器 test-page.html: 加 flv.js 播放器窗口（可选，纯语音时隐藏）

## 延迟预期
- 模式1（纯语音）: ~2-4s
- 模式2（+视频）: 声音 ~2-4s，视频 ~5-8s（TTS 1s + FlashHead 3s + RTMP 1s）

## 后续优化（不急）
- CosyVoice v3-flash 声音复刻：用姐姐音频克隆 CosyVoice 版姐姐声音，中英文都好
- v1/v2/v3.5 试听差异不大，复刻才是关键
- CosyVoice 流式 TTS + FlashHead 流式生成 → 降首帧延迟
- 智能切换：检测英文比例自动切 provider
