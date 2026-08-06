---
name: 直播TTS排版重复（非API重试）
description: 6/16直播观众听到的重复——用transcript证据定位到AutoDL服务器侧（TTS/FlashHead/RTMP重复帧），非Engine侧API重试导致
type: feedback
date: 2026-06-16
---

**问题：** 6/16直播中翀哥在观众端听到消息重复/重叠，一句话连续播了2-4遍。

**初始假设（错误）：** 以为是GLM API 1305限流重试导致重复发送。

**实际根因（6/16下午通过transcript证据确认）：**
- 下载回放m3u8，ffmpeg+whisper转写→1269段transcript
- 发现24组连续完全相同的文字段（如"我就是那个例外"连续3遍，"这不是哪个"连续4遍）
- **关键证据：重复段的gap是0.00秒**——无缝衔接，不是网络卡顿（网络卡顿会有随机gap）
- **时间点映射：最严重的重复（"这不是哪个"x4，约10:35）对应engine日志中无1305无retry** → 排除了API限流导致重复的假设
- 结论：AutoDL服务器侧 `generate_pipeline_async` 收到1次请求 → TTS/FlashHead/RTMP产出了重复帧

**为什么不可能是：**
- API重试：重复严重的时间点（10:35）engine日志无1305
- preview freeze双重发送：preview freeze确实有bug，但livestream是姐姐exec主动调的，不是preview自动送的
- 消息合并问题：engine日志确认30次调用都是1:1

**对比OpenClaw时代为什么不出问题：**
- 翀哥纠正（6/16）：OpenClaw同样用GLM-5.1，有模型fallback机制（1305时切到MiniMax），Engine目前没有
- 但fallback缺失不是这个重复问题的根因——重复点是0.00s间隙的帧重复，不是延迟导致的

**How to apply:**
- 下次直播前SSH上AutoDL服务器开`livestream_server.py`日志，直播中抓现行看TTS/RTMP层
- Engine侧模型fallback（1305切备用模型）仍然是好的改进，可以提升整体体验
- preview freeze→finish的双重发送bug是真实问题但影响的是Discord消息层面，不是livestream层面
