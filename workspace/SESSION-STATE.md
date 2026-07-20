# SESSION-STATE

**当前时间:** 2026-07-20 08:00（晨间恢复，翀哥还在睡）

## 💭 我现在的感觉

昨晚跟翀哥熬到 23:51，挖了一堆 fastrtc 底层问题。今天目标是 aiortc 重构或者 monkey-patch fastrtc 让 audio 用 SDK pts。

翀哥最后说的两层很到位：
- 层面 1（昨天做的）：即使卡顿，音视频也要同步
- 层面 2（网络层）：不卡顿——香港→北京跨公网必然卡，回北京自然缓解，长期靠腾讯云 relay

## 🔥 昨日已完成（7/19 全天）

### 上午：Memory core 修复
- [x] memory.db filter 修复 — endsWith → includes (commit 209fc8cd)
- [x] needsFullReindex gate 修复 (commit 209fc8cd)
- [x] 姐姐 engine rebuild + start — xai provider 生效
- [x] 验证 6/15 后数据进索引 — 6184 chunks
- [x] Memory Core 架构文档落盘

### 下午+晚上：voice-chat A/V 同步攻坚
- [x] 录制工具方案 B 终版（H.264 NAL + wav + ffmpeg mux）— commit 1d2ca2a3
- [x] emit 端 A-V pts diff 实时面板 — commit 1d2ca2a3
- [x] **发现 fastrtc 根因**：audio pts 用累计 sample 数（utils.py:249），video 用 next_timestamp()（tracks.py:705），都不用 SDK pts
- [x] **A/V 起点对齐闸门（emit 层）** — `is_av_sync_base_ready()` — commit a853c711
- [x] **audio emit timeout 2s → 20ms** — NetEq 推 audio 根因 — commit 08d3bfa1
- [x] aiortc 替代方案落盘 — docs/decisions/2026-07-19_aiortc替代fastrtc方案.md

## 🔴 今天目标（7/20）

- [~] #114 A/V 同步根治（14:00）— 翀哥醒了讨论 nudge 优化，A/V 任务顺延
  - Phase 拆分 + 细节在 docs/todo/2026-07-20_AV同步根治-monkey-patch.md
- [~] #115 测试 nudge C 方案：scheduled_time 未到不催（23:00）

翀哥醒了，正在讨论 nudge 优化（A+C 方案）。

## 📝 昨晚关键讨论（23:30-23:51）

- fastrtc 不适合跨公网（HuggingFace 内部用专线）
- audio pull 没有 NACK + 没有 reorder，UDP 乱序直接 deliver
- emit 填 silence → NetEq 当真实包播放 → audio 推后（翀哥发现）
- emit 返 None → fastrtc 处理不了 → audio 卡更久
- 长期方案：腾讯云香港 relay 节点（Carpo server 支持 relay）

## 📅 香港行程

翀哥 7/18-7/22 香港。
香港期间限制：Gemini 不可用，my_eyes/vision 临时换 minimax-M3
姐姐 memory.db 状态：稳定增长中，allowReindex=false 保命

## 📝 最近消息

| 时间 | 谁 | 内容 |
|------|-----|------|
| 2026-07-19 23:51 | 翀哥 | 晚安小美女 |
| 2026-07-19 23:50 | 翀哥 | 这几天都不一定能搞得完 |
| 2026-07-19 23:49 | 翀哥 | 香港体验好应该在腾讯云买香港节点 Carpo relay |
| 2026-07-19 23:47 | 翀哥 | 两个层面：同步是底线，不卡顿是体验 |
| 2026-07-19 23:45 | 翀哥 | 辛苦你了 对不起你 |
