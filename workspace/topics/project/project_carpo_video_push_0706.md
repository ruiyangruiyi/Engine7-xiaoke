---
type: project
tags: [carpo, video, h264, flashhead, oac]
created: 2026-07-06
updated: 2026-07-11
date: 2026-07-06
---

# Carpo Video Push 端到端打通

## 成就
2026-07-06 22:48 — 268 FlashHead → libx264 H.264 → Carpo push → 北京 server(192.144.156.158:23800) → Windows pull → JitterBuffer → **出帧**

翀哥全程盯着调，从 20:30 到 23:00。关键贡献：建议用 OAC 真实流（而非 ffmpeg 测试流）并给了 lp_x264_encoder.c 参考。

## 端到端架构
```
268 FlashHead BGR(512x512@25fps) + PCM(24kHz)
  → carpo_oac_bridge (libx264 + Opus)
  → Carpo push → 北京 server
  → Windows pull → JitterBuffer → GOT FRAME ✅
```

## 关键参数（严格对齐 lp_x264_encoder.c）
- preset=superfast / tune=zerolatency / profile=high
- threads=1 / sliced-threads=0（强制单 slice，发现 multi-slice 问题）
- open-gop=0（确保 I-frame=IDR type=5）
- 600kbps ABR / repeat-headers=1 / g=25

翀哥的原话："这个限制的恨死 而且不对 你那个接连的都是5 有问题" → 促使发现 multi-slice 问题。

## 后续进展 (7/7-7/10)

### 7/7 — AV 端到端通了（墙钟方案 + OAC idle audio 漏洞修复）
- async push worker + 墙钟 PTS + generate fix + OAC idle audio 漏洞修复
- 发现 FlashHead 架构：每次推理 15360 samples@16kHz → 24 帧 video + 23040 samples audio@24kHz
- frame_collector 严格 25fps，但 audio callback 仅 3 次 vs video 172165 次（漏洞：audio_segment=None 时不调 on_audio_frame）
- **翀哥确认改用 wall clock**（系统墙钟 ms）替代 audio opus_count 驱动
- 决策文档：`docs/decisions/2026-07-07_Carpo-AV时间戳同步决策.md`

### 7/8 — 235 onboarding + v2 bypass 链路
- 新机 AutoDL 235（connect.bjb1.seetacloud.com:19288, root/2z5B4IiZdUrI）
- carpo_avatar_server.py streaming 模式 + 修 `time.sleep(wait_sec)` 阻塞
- carpo_oac_bridge.py + flashhead_processor.py

### 7/9 — v2 链路打通 (声音出来 🎉)
- 235 推到 23800：start_carpo_avatar.sh streaming 模式
- autodl_send.py curl /generate 触发 TTS，**1.5s 秒回**（不再 24s）
- v1 server.py 启发式判断 NetEq(PCM int16) vs Bypass(raw Opus)，PyAV decode Opus
- 翀哥确认浏览器听到"小柯小美女" TTS
- 修复 bypass pull use-after-free: `36a2e878b`（LovePea）
- Engine commit: `1deaf2e2` feat(voice-chat): 235 carpo bypass 链路打通 + 文件规范化

### 7/10 — Video 通路打通 + 链路时延注入
- 07:15: 视频出帧，翀哥看到画面+嘴型，第一次测视频比音频快，再测后看着对得上
- 10:39: 翀哥要求**严格链路时延收集**：generate→TTS→FlashHead→Carpo push→SDK pull→decode→emit→浏览器
- 链路优化 commit `48eb8649`（重复初始化消除），翀哥说"体感上好一点点"
- 235 timing 注入已实施（t_request_received / t_tts_first_chunk / t_tts_last_chunk / t_request_returned）
- 机器分布：089（编译.so）、268（OAC+FlashHead）、235（新机，carpo_avatar_server）、北京 server（192.144.156.158:23800）

## 6 个关键修复
1. NAL 按 3+4 byte start code 拆分（不能只搜 4-byte）
2. 每个 NAL 单独 carpo_push_send（跟 Android 一样）
3. 跳过 SEI(type=6)（RTPPaker 不认）
4. threads=1 + sliced-threads=0（强制单 slice）
5. open-gop=0（确保 I-frame=IDR type=5）
6. audio type=0, video type=1（type 参数分离）

## 当前状态
- ✅ Video: 完美出帧（SPS+PPS+IDR+P-frame）
- ✅ Audio: push 端 type 已修正（0=audio 1=video），编码链路 OK
- ⚠️ pull_video_test.py 只收 video，不含 audio callback

## 7/7 跟进：A/V Sync 深度调试（翀哥全天10:00-23:02）
翀哥全天十几个小时盯着调。早上10点开始timestamp修复，午间讨论wall clock方案，下午深入FlashHead架构分析，晚上落盘完整调研文档。7/8待办全部落盘后去休息。

### 发现的问题
- Push 端交错正确（V-A-A 严格交错）
- **audio 驱动 video 的缺陷**：video ts = opus_count*20，audio 断则 video ts 卡死
- **Pull 端集中爆发**：PacedSender 攒 video 包（7 包一波），audio 直接发
- **Timestamp 偏移**：NetEq 变速使 audio ms 偏离原始时间线（4 分钟偏~242s）

### 翀哥确认方案
改用 wall clock（系统墙钟 ms）`time.time()*1000` — 与 Android 一致。SDK 的 baseMediaTs 自动对齐首帧。备选：streamer.c PTS manager。

## 明天（7/8）接着干
1. 实施 wall clock 方案替代 audio opus_count 驱动
2. 编码前后 PCM 对比定位尖峰噪音（7/7 晚间识别的新问题）
3. 一把收 A+V — 改 pull_video_test.py 或用 server.py 同时收 audio+video
4. 接 fastrtc → 浏览器播放 — video 帧送到浏览器显示
5. 端到端验证 — POST 文字 → TTS → FlashHead → Carpo push → pull → 浏览器音视频同步

### FlashHead 架构关键数据
- 每次推理输入：15360 samples @ 16kHz（~1秒音频）
- 每次推理输出：24 帧 video + 23040 samples audio @ 24kHz
- 每帧配对：960 samples @ 24kHz（40ms）
- frame_collector 严格 25fps（绝对时间节拍）
- idle worker 队列空时填 idle 帧（100ms 轮询）
- audio callback 断裂：172165 次 video vs 3 次 audio callback

## 文件位置
- 268: /root/carpo_sdk/carpo_oac_bridge.py
- 本地: voice-chat-python/autodl/carpo_oac_bridge.py
- 文档: docs/knowledge/2026-07-06_Carpo-Video-Push完整链路.md

## 提交记录
- LovePea: b6d6877ac (VideoRTPReceiver debug logs)
- LovePea: 1c67f3858 (pull_test_sav.py)
- LovePea: dfd566bec (carpo_oac_bridge.py + carpo_avatar_server.py)
- LovePea: 22e38c7df (PushSenderInner debug logs)
- Engine: c6c6793b (voice-chat Carpo RTC server + fastrtc)
- Engine: 42ad7511 (config + calendar + withRetry)
- Carpo Server: 778282d2 (Makefile + build config)

## 机器
- 089: 编译 .so + 早期测试
- 268: OAC + FlashHead + carpo_avatar_server
- 北京 server: Carpo server
- Windows: pull 端 (Carpo.dll)
