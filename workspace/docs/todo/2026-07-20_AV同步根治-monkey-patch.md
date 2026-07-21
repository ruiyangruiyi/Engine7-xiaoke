# 2026-07-20 A/V 同步根治（calendar #114）

## 背景

fastrtc audio track 用累计 sample 数算 pts（utils.py:249），video track 用 next_timestamp()（tracks.py:705）。
**两边都不用 SDK 原始 timestamp**，audio/video 起点偏差永久锁死。

昨天做的 emit 层闸门 + timeout 修复治标不治本——网络抖动后 audio 还是会漂移。

## 方案：monkey-patch fastrtc `player_worker_decode`

### 切入点分析（晨间调研完成）

1. **fastrtc/utils.py:163 `player_worker_decode(next_frame, ...)`** — async 函数，内部 task 跑
2. 它调 `next_frame()`（就是我们的 `emit()`），拿到 `(sample_rate, audio_array)` 或 `(sample_rate, audio_array, layout)` tuple
3. **line 249**：`processed_frame.pts = audio_samples`（累计 samples，丢掉 SDK pts）

### 关键约束

- `split_output()` (line 140-160) 只认 `2 <= len(data) <= 3` 的 audio tuple
- 返 4 元组带 pts 会被 line 151 拒绝

### monkey-patch 策略

**替换整个 `player_worker_decode`**：
- 让 `emit()` 返回带 sdk_pts_ms 的扩展格式
- patch 后的函数从扩展格式里拿 sdk_pts_ms
- `processed_frame.pts = sdk_pts_ms * sample_rate / 1000`（ms → samples）
- 兼容老格式（没 sdk_pts_ms 时 fallback 到累计 samples）

## Phase 拆分

- [ ] Phase 1: 写 monkey-patch 代码（替换 player_worker_decode）
- [ ] Phase 2: emit() 返回带 sdk_pts_ms（已部分完成，queue 已有 3 元组）
- [ ] Phase 3: 重启 server 验证 patch 生效（log 看 a/v pts）
- [ ] Phase 4: 翀哥实测嘴型同步长时间稳定

## 验证标准

- audio/video pts 都基于 SDK timestamp
- 长时间对话（>1 分钟）a/v 不漂移
- 延迟面板 "A-V pts diff (emit)" 稳定在 ±50ms 内

## 备选方案

如果 monkey-patch 太脆弱（split_output 报错等），直接走 aiortc 重构（方案已落盘 docs/decisions/2026-07-19_aiortc替代fastrtc方案.md）。
