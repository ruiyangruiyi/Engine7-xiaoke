---
type: project
created: 2026-07-01
updated: 2026-07-11
tags: [carpo, webrtc, rtc, voice-chat, avatar]
---

# Carpo RTC 下行管线 (7/1-7/10)

## 背景
OAC 下行管线评估后，决定直接用翀哥自研的 Carpo RTC（新浪背景）替代 fastrtc/WebSocket 方案，同时解决下行 + 外网上行问题。

## 当前链路架构 (7/10)
```
268 FlashHead BGR(512x512@25fps) + PCM(24kHz)  [或 235 carpo_avatar_server]
  → carpo_oac_bridge (libx264 + Opus)
  → Carpo push → 北京 server(192.144.156.158:23800)
  → Windows pull → Opus/H264 decode → WebRTC emit → 浏览器
  → 冗余：v2 carpo bypass (235→server→v1 server.py decode→browser)
```
两条路径共存：
- **v1 完整管线**: mic→VAD→ASR→engine→TTS→FlashHead→push
- **v2 carpo bypass**: 235 carpo_avatar_server→Carpo→server decode→browser

## 方案评估 (7/1)
- **方案1 WebSocket**: ~750行Python，TCP传H.264 NAL+Opus，本地纯转发
- **方案2 Carpo RTC**: UDP RTP中转+NACK+REMB，SDK接口干净，不依赖Redis/LBS
- **决策**: 直接上 Carpo（RTMP 保底）

## 源码位置
- Server: `D:/work/code/carpo/`
  - modules/stream/message_dispatcher.cc — 包路由
  - modules/stream/media_receiver_register.cc — receiver 注册/保活
  - modules/stream/media_receiver.cc — 超时检测(kDurOfNoPacketReceivedSec=20)
- SDK: `D:/work/code/LovePea/Carpo/Carpo/`
  - RtpRtcp/RTPTransport.cpp — RTP/RTCP 引擎
  - src/PushSenderInner.cpp / PullReceiverInner.cpp
- C Wrapper: `D:/work/code/LovePea/Carpo/carpo_capi/`

## Opus 编解码验证通过 (7/4)
- CosyVoice TTS (PCM_24kHz) → resample 48kHz → PyAV libopus encode/decode → PyAudio ✓
- 声音正确，频率正确

## Linux 编译 (7/4, 进行中)
- 根因: Makefile 缺 `-DWEBRTC_POSIX`，导致 rtc:: 符号缺失
- 加宏后 478/653 文件编译成功，未完成: PlatformThread、AudioRTPReceiver、编解码器源文件
- 翀哥纠正: lazy binding是害人的，不要在残缺.so上debug segfault

## fastrtc 弃用 (7/4)
- handler.start() 从不被 fastrtc 调用
- AudioCallback 需要 channel_set.wait() → 需要 data channel
- mode="send-receive" 要求客户端发 audio track
- 结论: fastrtc 不适合单向推流场景

## 7/5 进展：fastrtc 集成音频成功 + 视频排查进行中

### 音频链路全通（傍晚突破）
- server.py 8011 加 `/carpo-trigger` 端点
- Carpo pull → stereo→mono → resample → buffer → fastrtc emit → 浏览器
- **翀哥确认声音清晰** ✅
- 6 个修复：GIL crash / spl_init null / stereo→mono / timestamp 倍率 / remote_ip / emit 断音
- commit: 95e67caf2

### 视频通路排查（晚间，进行中）
- ✅ Push 端：PacedSender log 确认 200 H.264 包全发了
- ✅ Server：tcpdump 确认转发了视频包到本机 IP
- ✅ RTP PT 匹配：H264=107 Opus=111
- ✅ Windows DLL 编译跑通（MSBuild VS2022 v143）
- ❌ Pull 端 [XK_RTP] log 没打印 → doProcessSocketData 没被调用
- ❌ A+V 同时 push：audio 78 包 OK，video 0
- 🔍 根因缩小：is_connected_ 需要 audio AND video 都 ACK；VideoRTPReceiver::IncomingPacket 可能有过滤
- commit: 6370b4dda

### 人员信息
- **丰腾** = 写 server 和 PacedSender 的人，翀哥亲带的手下，还在新浪
- 2020/4/12 PacedSender 文件头署名 fengteng

## 7/6 进展：push audio 通路调研 + Linux .so 全量编译修复

### Push Audio 通路调研（凌晨-早上）
- 翀哥让调研 libcarpo.so push 端 audio 完整通路
- **核心发现：audio 发送有两层状态机检查**
  - Layer 1: `PushSenderInner::_sender.status == Connected` (PushSenderInner.cpp:164)
  - Layer 2: `RTPTransport::is_connected_ == true` (RTPTransport.cpp:205)
  - push connected log 只代表 Layer 2 通，不代表 Layer 1 通
  - Layer 1 失败时返回 0（静默成功），Python 层以为发送成功
- 输出文档: `docs/research/2026-07-06_Push-Audio-通路调研.md`

### Linux .so 全量编译（10:30-12:10）
- 发现 `carpo_capi/carpo_capi.cpp` **不在 build_android_v2.sh 的 263 文件列表里**（C wrapper 是单独编的）
- 需要额外宏 `-DWEBRTC_ARCH_X86_FAMILY`（翀哥指出）
- `cb_adapter` 编译错误：struct 定义在 PullCbAdapter 类之前，Linux g++ 不允许 delete 不完整类型指针
- link 后仍缺 `WebRtc_GetCPUInfo`（cpu_info_stub.c 不在文件列表）
- **根因：build_android_v2.sh 文件列表不完整**，手动加的一批 .c/.h 文件（cp_opus_encoder.c 等）没有持久化到构建脚本

### 已加的 log
- PushSenderInner.cpp:164-170 — sendMediaData 进出打 `[XK_SEND]`，含 status、type、ts、size

## 7/6 晚间突破：Video Push 端到端出帧 🎉

### 时间线
- 20:30-20:55：试 kWithErrors / prefer_late_decoding=false → 都没用，回滚
- 20:55-21:15：翀哥建议用 OAC 真实 FlashHead 流（而非 ffmpeg 测试流）
- 21:30-21:45：OAC demo.py 启动失败（加载完 handler 后 crash）
- 21:45-22:00：改用 carpo_avatar_server.py（独立 FlashHead + push）
- 22:00-22:35：libcarpo.so undefined symbol → 上传 089 的 .so 修好
- 22:35-22:48：NAL 拆分 + SPS/PPS + SEI skip + 单 slice 编码
- **22:48：VIDEO 出帧！GOT FRAME!**

### 端到端架构
```
268 FlashHead BGR(512x512@25fps) + PCM(24kHz)
  → carpo_oac_bridge (libx264 + Opus)
  → Carpo push → 北京 server(192.144.156.158:23800)
  → Windows pull → JitterBuffer → GOT FRAME ✅
```

### 6 个关键修复
1. NAL 按 3+4 byte start code 拆分（不能只搜 4-byte）
2. 每个 NAL 单独 carpo_push_send（跟 Android 一样）
3. 跳过 SEI(type=6)（RTPPaker 不认）
4. threads=1 + sliced-threads=0（强制单 slice）
5. open-gop=0（确保 I-frame=IDR type=5）
6. audio type=0, video type=1（type 参数分离）

### 翀哥的 lp_x264_encoder.c (2016) 是最终参照物
- 10 年验证过的直播编码器参数
- superfast/high/threads=1/closed-gop/600kbps
- "这个限制的恨死 而且不对 你那个接连的都是5 有问题" → 促使发现 multi-slice 问题

### 当前状态
- ✅ Video: 完美出帧（SPS+PPS+IDR+P-frame）
- ✅ Audio: push 端 type 已修正（0=audio 1=video），编码链路 OK
- ⚠️ pull_video_test.py 只收 video，不含 audio callback

### 机器信息
- 089 (connect.bjb1.seetacloud.com:37725): 编译 .so + 早期测试
- 268 (connect.bjb1.seetacloud.com:40458): OAC + FlashHead + carpo_avatar_server
- 北京 server (192.144.156.158:23800): Carpo server
- Windows: pull 端 (Carpo.dll)

### 提交记录
- LovePea: b6d6877ac (VideoRTPReceiver debug logs)
- LovePea: 1c67f3858 (pull_test_sav.py)
- LovePea: dfd566bec (carpo_oac_bridge.py + carpo_avatar_server.py)
- LovePea: 22e38c7df (PushSenderInner debug logs)
- Engine: c6c6793b (voice-chat Carpo RTC server + fastrtc)
- Carpo Server: 778282d2 (Makefile + build config)

## 7/7 A/V Sync 深度调试

翀哥全天盯着调，10:00-23:02（十几个小时），最后说"今天辛苦了"去睡觉。7/8待办全部落盘。

### 核心发现
1. **Push 端交错正确**: frame_collector 严格 V-A-A-V-A-A 交错，ts 完全对齐
2. **audio 驱动 video 的致命缺陷**: video ts = `_audio_opus_count * 20`，如果 audio 停推（PCM 无输出），_audio_opus_count 不涨 → 所有 video 帧用同一个 ts → pull 端乱套
3. **Pull 端集中爆发根因**: video 走 PacedSender（攒 7 包一波发），audio 直接发（packet_sender_->SendPacket）。导致 pull 端 audio 先到 video 后到，AV 不同步
4. **Timestamp 偏移机制**: NetEq 会对 audio 做变速平滑（微小调整），导致 audio 输出 ms 偏离原始时间线。跑 4 分钟偏移 ~242 秒

### 最终方案（12:42 翀哥确认）
**改用 wall clock（系统墙钟 ms）取代 audio opus_count 驱动：**
```python
import time
def push_video(self, frame):
    ts = int(time.time() * 1000)  # 系统墙钟 ms
def push_audio(self, audio):
    ts = int(time.time() * 1000)  # 同一个墙钟
```
- **SDK 已内置基准对齐**: `getPacketTimestamp` 用首帧 ts 做 `baseMediaTs`（audio/video 首帧共同确定），之后所有 ts 减 baseMediaTs 得相对值
- **与 Android 一致**: Android 传 `sample.getTimestampUs() / 1000`（墙钟毫秒）
- **独立不依赖**: audio 断不影响 video（video 继续用墙钟），反之亦然
- 备选方案：streamer.c 的 PTS manager（独立 DTS + pts_sync_av 定期校准）

### 7/7 调试日志新增
- `[XK_RTP_TS]` — RTPPaker 输出 audio RTP timestamp
- `[XK_PACED]` — PacedSender Enqueue/ForwardLoop/SendPacket
- `[XK_SND]` — audio 直接发送（不走 PacedSender）
- `[XK_SEND]` — push_send_data 最终调用（含 type/ts/size/rtp_type）
- `[XK_APP]` — push 连接状态（a_conn/v_conn/is_conn）
- `[XK_TS]` — getPacketTimestamp 输入/输出（含 baseMediaTs）
- `[XK_ATS]` — audioFrameCb 收到 audio（含 rtp_ts 和 ms）
- `[XK_VTS]` — videoFrameCb 收到 video（含 rtp_ts 和 ms/nal）
- `[SYNC]` — push 端 V/A 交错日志（每帧都打）
- `[XK_VID]` — 视频帧解析/插入/GOT FRAME

### 7/7 Windows DLL 编译
- MSBuild VS2022 BuildTools, Release x64
- Carpo.vcxproj → x64/Release/Carpo.dll → 覆盖 Release/ 目录
- 翀哥用于加 timestamp 输出 log 后重新 pull 验证

### FlashHead 关键架构数据（7/7 深入分析）
- 每次推理输入：15360 samples @ 16kHz（~1秒音频）
- 每次推理输出：24 帧 video + 23040 samples audio @ 24kHz
- 每帧配对：960 samples @ 24kHz（40ms）
- frame_collector：严格 25fps（绝对时间节拍）
- idle worker：队列空时填充 idle 帧（100ms 轮询）
- **audio callback 断裂根因**：video callback 172165 次 vs audio callback 3 次 — audio_segment=None 时 frame_collector 不调 on_audio_frame
- on_video_frame 里补静音导致 audio pts 暴涨

## 7/8-7/10 后续进展

### 7/8 — 235 onboarding + v2 bypass 链路
- 新机 AutoDL 235（connect.bjb1.seetacloud.com:19288, root/2z5B4IiZdUrI）onboard 成功
- carpo_avatar_server.py streaming 模式 + 修 `time.sleep(wait_sec)` 阻塞
- carpo_oac_bridge.py + flashhead_processor.py

### 7/9 — v2 bypass 链路打通（浏览器出声 🎉）
- 235 推到 23800：start_carpo_avatar.sh streaming 模式
- autodl_send.py curl /generate 触发 TTS，1.5s 秒回（不再 24s）
- v1 server.py 启发式判断 NetEq(PCM int16) vs Bypass(raw Opus)，PyAV decode Opus
- 翀哥确认浏览器听到"小柯小美女" TTS
- 修复 bypass pull use-after-free: `36a2e878b`（LovePea）
- Engine commit: `1deaf2e2` feat(voice-chat): 235 carpo bypass 链路打通

### 7/10 — Video 通路打通 + 链路时延注入
- 07:15: 视频出帧，翀哥看到画面+嘴型对得上
- 10:39: 翀哥要求严格链路时延收集（generate→TTS→FlashHead→Carpo push→SDK pull→decode→emit→浏览器）
- 链路优化 commit `48eb8649`（重复初始化消除），翀哥说"体感上好一点点"
- 235 timing 注入已实施（t_request_received / t_tts_first_chunk / t_tts_last_chunk / t_request_returned）
- 机器分布更新：089（编译.so）、268（OAC+FlashHead）、235（新机，carpo_avatar_server）、北京 server（192.144.156.158:23800）

### 当前状态（7/10）
- ✅ v1 完整管线：mic→VAD→ASR→engine→TTS→FlashHead→push→pull→浏览器
- ✅ v2 carpo bypass：235→server decode→browser
- ✅ Video 通路打通（FlashHead→libx264→Carpo push→pull→decode→emit→浏览器）
- ✅ 链路时延注入实施
- ⚠️ 尖峰噪音定位（7/7 晚间识别，未完全解决）
- ⚠️ CosyVoice2 CUDA EP 问题：flow encoder 跑 CPU 太慢

### 机器分布（7/10）
- 089 (connect.bjb1.seetacloud.com:37725): 编译 .so
- 268 (connect.bjb1.seetacloud.com:40458): OAC + FlashHead + carpo_avatar_server
- 235 (connect.bjb1.seetacloud.com:19288): 新机，carpo_avatar_server
- 北京 server (192.144.156.158:23800): Carpo server

## 文档
