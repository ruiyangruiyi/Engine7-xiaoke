# aim: voice-chat /stop endpoint

## 目标
1. Python server.py 加 `/stop` endpoint：清空 _audio_queue + 取消正在跑的 TTS asyncio task + 重置 PTS
2. Python `/stop` 同时通知 engine 中断 LLM query（POST engine 的 abort 机制或直接调 interrupt）
3. 验证：voice-chat 正在说话时调 `/stop`，音频立即停止，LLM query 被中断，下一轮 query 不受影响

## 元信息
- 频道: feishu
- 指派: 小柯（自己）
- 创建时间: 2026-06-28 19:57
- 完成时间: 2026-06-28 21:18
- 状态: ✅ 已达成

## 验收结果
- ✅ 飞书 /stop → engine interrupt + POST python → 清队列 + cancel TTS callback + reset PTS
- ✅ 浏览器"🤫请先别说"按钮 → POST python /stop → 同上 + POST engine stop
- ✅ TTS线程cancel: _cancelled flag 拦截 _push_chunk（executor线程不能强杀）
- ✅ 日志验证: [stop] Cancelled TTS callback + Audio queue cleared + PTS reset + engine.interrupt()

## 进度记录
2026-06-28 20:05 | 代码完成，commit 08c528c。Python /stop + engine /webhook/voice-chat/stop。等翀哥 rebuild 验证。
2026-06-28 20:35 | 第一次验证：stop 触发了但 TTS 线程没停。根因：executor线程cancel不了。
2026-06-28 20:42 | 修复：_cancelled flag 拦截 _push_chunk。commit bfa6afb。
2026-06-28 20:53 | 第二次验证通过：日志确认 cancel callback + clear queue + reset PTS。frame max值降到静音。
2026-06-28 20:56 | 加"🤫请先别说"按钮。commit 5058352。
2026-06-28 21:00 | engine /stop 也通知 Python 停 TTS（解决 LLM 已完成但 TTS 还在播放）。commit f620848。
2026-06-28 21:10 | 模型切换 glm-4.5-air，延迟55s（太慢，后续评估）。
2026-06-28 21:18 | 完成，基线v2确立。
