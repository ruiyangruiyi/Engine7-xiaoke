# Voice-Chat + Carpo 项目进度（截至 2026-07-09）

> 小柯从落盘文档梳理，给翀哥的进度快照

## 整体定位

实时语音/视频聊天管线 = VAD+ASR → Engine → TTS → 推流（Carpo RTP）→ Pull 端 → 播放
264 老方案是 RTMP+FlashHead，新方案走 Carpo SDK 走 RTP，绕开 RTMP 中间层。

---

## ✅ 已完成

| 模块 | 日期 | 状态 |
|------|------|------|
| Carpo SDK 编译 (VS2022 v143, 175 文件) | 7/2 | ✅ |
| Carpo C Wrapper (8 个 extern "C") | 7/2 | ✅ |
| Python ctypes 绑定 (CarpoPusher) | 7/2 | ✅ |
| Carpo Server Docker 跑通 23800/UDP | 7/2 | ✅ |
| 推流验证（真实 UDP + 事件回调） | 7/2 | ✅ |
| 新浪痕迹清理 | 7/2 | ✅ |
| autodlv2 部署包（TTS+Avatar+livestream） | 7/2 | ✅ |
| Video 端到端出帧 | 7/6 | ✅ (NAL 拆分+SPS/PPS/SEI skip+单 slice+closed GOP+x264 superfast) |
| x264 参数对齐 lp_x264_encoder.c | 7/6 | ✅ (superfast/high/threads=1/closed-gop/open-gop=0/600kbps) |
| Audio + Video 双向 SDK 路径 | 7/6 | ✅ (video 走 PacedSender, audio 直发) |
| Voice-Chat server.py 完整管线 | 7/2 | ✅ (VAD+ASR+Engine+TTS 全跑通) |
| FlashHead + AutoDL 推流 | 7/2 | ✅ (CosyVoice 流式 TTS → FlashHead → RTMP) |

---

## 🔲 当前瓶颈（按优先级）

### 1. Pull 端 audio 尖峰噪音 🔥
- **现象**：NetEq 解码后 PCM 有尖峰/电流音
- **已验证**：push_pre_opus.pcm 干净 / push_post_opus.opus 干净 / neteq_pre_mono.pcm 干净 / **neteq_out.pcm 不干净** ❌
- **2ch vs 1ch 都不干净**（不只是声道问题）
- **决策**（7/8 调研）：绕过 NetEq，callback 收原始 Opus 字节
- **方案 C**（推荐）：AudioRTPReceiver::popAndDecode 加 pkt_buffer 分支返回 raw bytes
- **当前状态**：方案 C 已实施，但**昨天 stash 了**（因为调试验证时遇到崩溃），现在 HEAD 跑的是纯净 NetEq HEAD DLL 验证链路（500 个真包收得到）

### 2. Push 端 AV 同步（PTS）⚠️
- **现象**：video pts = audio pts × 5 左右
- **已实现**：独立 _video_pts + _audio_pts 计数器，各自 +40ms/帧
- **待验证**：frame_collector 是否真的 25fps（在 callback 入口加 wall timestamp 打）
- **若 frame_collector 失效**：查为什么绝对时间节拍失效

### 3. Voice-Chat 集成到 voice-chat 模块 ⏸️
- Carpo 替代 WebRTC 接入未做
- 浏览器 fastrtc 编码未替换
- AEC/AGC/NS 暂未编（推流端用不着，双向时再加）

---

## 🔧 调试工具栈（今天搭好）

- **faulthandler**：Python 看 DLL native crash traceback
- **PDB（9.5MB）**：Release|x64 加 /Zi /DEBUG 编译，符号表解偏移

---

## 📂 关键文档索引

- 进度总览：docs/knowledge/Voice-Chat进度总览.md
- Push 链路总结：docs/knowledge/2026-07-06_Carpo-Video-Push完整链路.md
- Pull 旁路方案：docs/knowledge/2026-07-08_Carpo-pull-Opus-bypass.md
- AV 时间戳调研：docs/decisions/2026-07-07_Carpo-AV时间戳同步决策.md
- Push 通路 debug：docs/research/2026-07-06_Push-Audio-通路调研.md
- 视频根因：docs/research/2026-07-06_视频根因深挖.md
- 视频通路排查：docs/research/2026-07-05_Carpo视频通路排查.md
- AV Sync 决策：docs/decisions/2026-07-07_Carpo-AV时间戳同步决策.md
- AutoDL 部署：docs/decisions/2026-07-04_AutoDL推流服务_Carpo版.md
- 移动端调研：docs/research/2026-07-05_Android-iOS-Push代码调研.md
- SDK 接口：docs/knowledge/Carpo-C-Wrapper-ctypes接口.md

---

## 🚀 今天要做的事

1. ~~搭 faulthandler + 编带 PDB 的 DLL~~ ✅（7/9 早）
2. 在 268 上循环推 TTS，看 pull 端能不能稳定收到（验证链路）
3. 用 PCM 写文件对比定位尖峰噪音到底是 Opus 编码里产生的还是别的地方

---

## 📦 当前 268 状态

- 机器：AutoDL RTX 4090
- SSH：connect.bjb1.seetacloud.com:40458, root/NIgDNE+SPYSM
- /root/carpo_sdk/：libcarpo.so + carpo_oac_bridge.py
- /root/autodl-tmp/envs/：flashhead + gptsovits
- 启动脚本：start_carpo_avatar.sh（voice-chat-python/autodl/）
- 我刚推的：/root/carpo_sdk/_loop_tts_demo.py（CosyVoice 流式循环 TTS）