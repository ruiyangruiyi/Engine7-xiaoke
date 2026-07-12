# 2026-06-29 voice-chat Avatar 集成

## 来源
6/28 晚翀哥讨论定方向。方案详情见 `docs/decisions/2026-06-28_voice-chat-avatar-integration.md`

## 任务清单

- [~] **1. AutoDL livestream_server.py 加 CosyVoice TTS 选项** — started 6/29, updated 7/1
  - ✅ 代码写完：call_tts_cosyvoice() + call_tts(provider) + tts_config.json
  - ⚠️ 待确认：AutoDL 能否 pip install dashscope
  - ⚠️ 待测试：SSH 部署 + 实际调用

- [~] **1.5. 修复 reload_avatar idle_25fps.mp4 编码问题** — 7/1 ✅
  - ✅ cv2 mp4v → ffmpeg libx264（Main profile, bframes=0, 静音AAC）
  - ✅ FlashHead Tensor → numpy 转换
  - ✅ AutoDL 268 机实测通过，avatar 切换成功（xiaoke.jpg）
  - commit: b9ababa → c62bf46 → 80e1091

- [ ] **2. voice-chat bridge 对接 AutoDL**
  - ✅ autodl_avatar.py 已写完（SSH + livestream_send.py pipeline）
  - ✅ /avatar/config 端点可切换 image 和 tts_provider
  - ⚠️ 待测试：从 voice-chat 本地端发起切换

- [ ] **3. 浏览器加视频播放窗口**
  - test-page.html 嵌 flv.js，播 HTTP-FLV (http://192.144.156.158:8080/live/stream.flv)
  - 纯语音时隐藏

- [ ] **4. 全链路测试**
  - 文本 → AutoDL TTS → FlashHead → RTMP → SRS → 浏览器
  - 测延迟，看体验

- [ ] **5. CosyVoice 换声音实测**
  - AutoDL 上 dashscope SDK 安装
  - call_tts_cosyvoice() 实跑验证

## 备注
- 先跑通 RTMP，后面考虑 SRS WebRTC 转发降延迟
- 可复用 `skills/my-livestream/livestream_send.py` 的 SSH 全流程
- AutoDL 需要先开机
