---
type: reference
created: 2026-06-25
updated: 2026-06-27
tags: [OAC, webrtc, vad, asr, avatar]
---

# OAC 架构与嵌入方案 (6/25-6/27)

## 定位
翀哥6/25："先跑通OAC原生模式感受下效果，以后移植是标准不能比它差"
6/27："一步一步复刻OAC机制，直接搬，优化在后面先看效果"

## OAC 语音切分三层机制
1. **POST_END 监控（核心）**: VAD 四状态 PRE_START→START→END→POST_END。POST_END 继续监听 1 秒，有新语音+间隔<0.5s→cancel旧stream重连
2. **Smart Turn EOU 模型**: smart-turn-v3.1 ONNX 判断"说完了吗"
3. **音频累积重连**: accumulated_speech_audio 从说话开始一直累积

## OAC 源码位置
- VAD: D:/work/OpenAvatarChat/src/handlers/vad/silerovad/
- EOU: D:/work/OpenAvatarChat/src/handlers/vad/smart_turn_eou/

## OAC Docker 部署坑 (6/25)
1. git submodule 没拉 → LiteAvatar 空目录
2. 模型文件缺失 → 手动 download_avatar_model.py
3. paraformer 权重缺失 → download_models.py --handler liteavatar
4. LiteAvatar init 286 秒 → 每 session fork 新进程崩溃
5. duplex agent 配置太重 → SenseVoice 反复加载
6. ASR 中文乱码 → Docker locale POSIX，SenseVoice 没传 language="zh"
- 修复: `LANG=C.UTF-8 LC_ALL=C.UTF-8` + handler 传 `language="zh"`

最终 simple 配置（disable LiteAvatar）跑通：WebRTC→VAD→ASR→LLM→TTS

## oac-bridge 验证
- curl POST `http://127.0.0.1:16990/webhook/oac-bridge` → `{"ok":true}`
- engine 创建 session `oac:test-from-curl` 成功
- engine webhook 异步（立即返回 ok，LLM 完后 POST 回 callback）
