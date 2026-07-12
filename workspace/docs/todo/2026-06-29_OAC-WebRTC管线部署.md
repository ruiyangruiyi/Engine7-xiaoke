# OAC WebRTC 管线 — AutoDL 4090 部署方案

**日期：** 2026-06-29
**状态：** 方案设计
**参与者：** 翀哥 + 小柯

## 背景

现有 RTMP 管线（livestream_server + C streamer）延迟已到 2s 极限。
新起 OAC WebRTC 管线作为第二条独立管线，不改现有方案。

## 架构

```
Engine (本地 Windows)
  → LLM 生成文字回复
  → livestream_send.py SSH curl 发文字到 AutoDL

AutoDL 4090
  ├─ livestream_server.py (:8899)  ← RTMP 管线（保留不动）
  └─ OAC (:8282)                    ← WebRTC 管线（新建）
       接收文字 (HTTP POST)
       → CosyVoice TTS 流式合成
       → FlashHead processor 攒 1s 音频推理
       → frame_collector 25fps 逐帧输出
       → fastrtc + aiortc → WebRTC
       → SRS → 浏览器
```

## Engine 侧（不改）

livestream_send.py 加路由参数：
- `--mode rtmp`（默认）→ POST localhost:8899（现有）
- `--mode oac` → POST localhost:8282（新增）

engine 侧 flashhead.py 不感知管线差异，只管发文字。

## OAC 侧改造

### 要改什么

1. **LLM handler → 替换为文字接收端**
   - OAC 原有 LLM handler（百炼 qwen-plus API）不要
   - 新增一个 HTTP 接收端：收到文字 → 直接喂 TTS handler
   - 或者：写一个最小的 custom LLM handler，等 HTTP POST 推文字进来

2. **ASR + VAD → 可选**
   - 如果 OAC 端不做语音输入（文字进），ASR/VAD 不需要
   - 如果以后要双向语音，保留 OAC 自带的 SenseVoice + Silero VAD

3. **TTS → CosyVoice（百炼 API）**
   - OAC 自带 cosyvoice handler，已有流式 on_data → submit_data
   - 直接用

4. **FlashHead → 不改**
   - flashhead_processor.py 原样用
   - 模型路径指向 AutoDL 上已有的 SoulX-FlashHead

5. **WebRTC 输出 → fastrtc + SRS**
   - OAC 的 RtcClient handler 原样用
   - 浏览器连 OAC WebRTC 端口
   - 或者 OAC → SRS（如果需要 CDN 分发/多观众）

### 配置文件

基于 `chat_with_openai_compatible_bailian_cosyvoice_flashhead.yaml` 改：
- 去掉 LLM handler（或换成文字接收 handler）
- 去掉 ASR/VAD handler（文字进，不需要语音识别）
- 保留 CosyVoice TTS + FlashHead + RtcClient
- FlashHead 模型路径指向 `/root/SoulX-FlashHead`

## AutoDL 目录结构

```
/root/autodl-tmp/
├── livestream_server.py        ← RTMP 管线（不动）
├── continuous_streamer/         ← C streamer（不动）
├── GPT-SoVITS/                  ← GPT-SoVITS（不动）
├── OAC/                         ← 新建
│   ├── OpenAvatarChat/          ← OAC 仓库（git clone）
│   ├── configs/
│   │   └── text_input_flashhead.yaml   ← 定制配置（文字进→WebRTC出）
│   ├── models/
│   │   ├── SoulX-FlashHead-1_3B/       ← 软链到现有模型
│   │   └── wav2vec2-base-960h/         ← 软链到现有模型
│   ├── start_oac.sh             ← 启动脚本
│   └── logs/
└── envs/
    ├── flashhead/               ← FlashHead venv（现有）
    └── oac/                     ← OAC venv（新建，含 fastrtc/aiortc）
```

## 关键技术问题（待验证）

1. **fastrtc/aiortc 在 AutoDL 上能否跑通**
   - AutoDL 有端口映射，但 WebRTC 需要 UDP 端口
   - STUN/TURN 是否必须
   - AutoDL 端口映射支不支持 UDP

2. **H.264 硬件编码**
   - OAC 有 NVENC 配置代码（client_handler_rtc.py）
   - 4090 支持 NVENC，但需要验证 ffmpeg/x264 编译支持

3. **文字接收接口**
   - 最简单：写一个 Flask/FastAPI 接收 POST
   - 收到文字 → 调 OAC engine 的 TTS handler
   - 或者：custom handler 继承 OAC 的 handler 体系

4. **SRS 对接**
   - WebRTC → SRS 需要信令对接
   - 或者浏览器直连 OAC WebRTC（单客户端，不做分发）

## 验证标准

- [ ] AutoDL 上 OAC 能启动，FlashHead 模型加载成功
- [ ] POST 文字 → OAC 收到 → TTS 合成 → FlashHead 出帧
- [ ] 浏览器能看到 WebRTC 视频流
- [ ] 端到端延迟 < 3s（文字发出到画面出现）
- [ ] 长回复流式不断帧

## 下一步

等翀哥指示具体执行步骤。
