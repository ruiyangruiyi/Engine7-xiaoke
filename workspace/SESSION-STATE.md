# SESSION-STATE.md - 当前工作状态

## 当前时间
2026-07-07 23:00 (Asia/Shanghai)

## 🎯 当前任务：Carpo 音视频管线

### 今日成果（7/7）
- ✅ **async push worker** — callback 只 put queue，编码推流在后台线程
- ✅ **墙钟 PTS** — 删除计数器，统一 `int((time.time() - _start_wall) * 1000)`
- ✅ **generate fix** — c24k 长度严格匹配，zero-pad 补齐
- ✅ **OAC idle audio 漏洞修复** — speaking 分支 audio_segment=None 时补 np.zeros
- ✅ **AV 端到端通了！** video 眨眼动嘴 + audio 能听清说话
- ✅ **6 个 commit** — dfd566bec / b5319b73c / 04df17e09 / b7bc8fbfb / 7c152dcfb + fprintf 注释
- ✅ **Carpo.dll 重编译** — XK_ fprintf 全注释，去掉 debug log 噪音

### OAC 源码关键发现
- FlashHead `_idle_inference_worker` — 内部 `_make_ambient_noise` 生成呼吸噪声，输出 idle 微动 video
- `frame_collector` idle 分支（item=None）— 也调 on_audio_frame(np.zeros)
- **OAC 漏洞**：idle worker 生成的 item 有 video 但 audio_segment=None → 走 speaking 分支 → 不调 audio callback → audio 断推
- `on_speech_end` 回调 — 可用于保活/状态切换（暂未接）
- `FrameQueueItem` — video_frame + audio_segment + speech_id + end_of_speech

### 明天继续
- [ ] **push 端编码前后 PCM 写文件对比** — 定位尖峰噪音在哪步产生
  - Opus 编码前 PCM → 写文件1
  - Opus 编码后包 → 写文件2
  - pull 端 PCM → 已有 received_audio.pcm
  - ffplay 波形对比
- [ ] 方案1完善：PyAV video decode（VideoFrame not iterable 错误）
- [ ] 方案2：接 fastrtc 浏览器（audio track 已有，加 video track）
- [ ] 接 on_speech_end 回调做保活/状态切换
- [ ] 验证 TTS 停了能撑多久（RTCP 保活极限）

### 关键文件
| 文件 | 位置 |
|------|------|
| carpo_oac_bridge.py | voice-chat-python/autodl/（268 + 本地） |
| carpo_avatar_server.py | voice-chat-python/autodl/ |
| pull_video_test.py | Carpo/carpo_capi/python/（存 .h264） |
| pull_play_auto.py | Carpo/carpo_capi/python/（pyaudio 播放+存 PCM） |
| pull_decode_play.py | Carpo/carpo_capi/python/（PyAV 解码→mp4） |
| flashhead_processor.py | OAC 原版 + patch（audio_segment=None 补 np.zeros） |

### 关键环境
| 项目 | 值 |
|------|-----|
| AutoDL 268 | connect.bjb1.seetacloud.com:40458 root/NIgDNE+SPYSM |
| 北京 Server | 192.144.156.158:23800 (Docker carpo_server) |
| Server 代码 | D:/work/code/Carpo/ (bazel build) |

## 💭 我现在的感觉
2026-07-07 23:00。今天超大丰收。从早上 async worker 到晚上 AV 端到端通了——video 眨眼动嘴 + audio 能听清说话。翀哥的墙钟方案 + idle audio 漏洞发现是两个关键转折点。现在只剩尖峰噪音问题，明天编码前后对比一下就知道了。翀哥 22:59 说的最后一件事是编码前后对比 PCM。他辛苦了一天，应该去休息了。

## 📝 最近消息
2026-07-07 22:59 | 翀哥 | 编码前后写文件对比，明天干
2026-07-07 22:57 | 翀哥 | pcm立体声和单声道都有尖音，不是pyaudio的锅
2026-07-07 22:36 | 翀哥 | "起码声音是对的 就是有高频尖音"
2026-07-07 22:25 | 翀哥 | "能听清说话"
2026-07-07 22:23 | 翀哥 | A=1579 audio 收到了！
2026-07-07 22:17 | 翀哥 | 指出 audio_segment=None 不 push 的漏洞
2026-07-07 18:59 | 翀哥 | "搞吧 方向看来没错"
2026-07-07 18:42 | 翀哥 | idle frame 也发 np.zeros 静音 audio
2026-07-07 18:40 | 翀哥 | "提交吧这次 应该是真行了"
