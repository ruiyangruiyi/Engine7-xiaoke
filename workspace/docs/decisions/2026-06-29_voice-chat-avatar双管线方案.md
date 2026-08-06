# Voice-Chat Avatar 双管线方案

**日期：** 2026-06-29
**参与者：** 翀哥 + 小柯

## 背景

Voice-chat avatar 需要降低端到端延迟。现有 RTMP 方案延迟 4-7s，瓶颈在 LLM(3-4s) + TTS 整段等待 + RTMP 缓冲。

## 决策：两条独立管线，不融合

### 管线 1：RTMP 方案（现有，保留）
- livestream_server.py + C streamer + wav 文件
- FlashHead chunk-by-chunk 推帧到 Unix socket
- C streamer 读 wav 做音频，mux 到 RTMP
- 已跑通，commit 54140c8 + 8430c90
- 延迟：4-7s（batch→streaming 已优化 60%+）

### 管线 2：OAC 方案（新建）
- 直接用 OAC 的 FlashHead processor 架构
- 流式 TTS → processor 攒够 1s 音频 → FlashHead 推理
- 音视频逐帧配对（FrameQueueItem）
- 走 WebRTC，不走 RTMP/C streamer
- 理论延迟更低：去掉 RTMP 缓冲 1-2s

## ⚠️ C streamer 不要动
C streamer 的时序调了两周，非常独特：
- FlashHead 生产速度 ~100fps，消费 25fps，生产远超消费
- 不能匀速推，需要有余量
- 超速推的帧要在后面的间隔里补回来
- 要兼容各种播放器的 buffer，不能让播放器时序出问题（丢帧/卡顿/缓冲）
- LIVE_BEGIN/END 时序、idle flush 都有坑

**结论：管线2另起炉灶，C streamer 一行不碰。**

## OAC 关键架构（flashhead_processor.py）
- `add_audio()`: TTS 流式 PCM chunk → 攒到 `_pending_audio`
- 攒够 `audio_slice_samples`（15360 = 24帧 × 16000/25）→ 推理
- `_process_chunk()`: FlashHead 推理 → 每帧配一段音频 → FrameQueueItem 入队
- `frame_collector`: 25fps 逐帧取，callback 视频+音频
- idle worker: 不说话时生成呼吸动画
