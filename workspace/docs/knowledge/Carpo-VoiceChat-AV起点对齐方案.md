# Carpo-VoiceChat A/V 起点对齐方案

## 背景

voice-chat 浏览器看到的 avatar video 与 audio 不同步：video 快，audio 滞后。

## 根因（7/19 翀哥发现）

**audio/video 起点不同步 + 各自用本地时钟算 pts**：

- `fastrtc/utils.py:249` — `processed_frame.pts = audio_samples`（累计 sample 数，与 SDK pts 无关）
- `fastrtc/tracks.py:705` — `pts, time_base = await self.next_timestamp()`（本地 monotonic clock）

两边都用本地时钟自己算 pts，**不用 SDK 原始 timestamp**。

如果 video 第一帧比 audio 第一帧早到 N ms，后续 fastrtc 给它们的 pts 各自从 0 开始累加，**永远差 N ms**，浏览器渲染就错位 N ms。

实测：SDK pull 端 A-V pts diff = 280ms，emit 端 = 200ms。fastrtc 不用 SDK pts 是根因。

## 方案：A/V 起点对齐闸门（已验证有效）

**核心思路**：不修改 fastrtc 内部 pts 计算，只在 emit 层做闸门——a/v 都到了再放行。

### 机制

1. **全局状态**：
   - `_av_aligned = False`（对齐未完成）
   - `_a_first_seen_ts = None`（audio 第一帧 sdk_pts_ms）
   - `_v_dropped_before_align = 0`（对齐前丢的 video emit 次数）

2. **video_emit 层**：
   - 如果 `not _av_aligned` 且 `_a_first_seen_ts is None` → 返回 black frame（丢这帧）
   - 如果 `not _av_aligned` 且 `_a_first_seen_ts is not None` → 设 `_av_aligned = True`，放行
   - 已对齐 → 正常 emit

3. **audio emit 层**：
   - 第一次拿到 sdk_pts_ms → 记 `_a_first_seen_ts`
   - 后续帧 → 正常 emit（audio 不丢，buffer 在 queue 里等对齐）

### 为什么这样有效

- video 丢帧是**解码后**丢的（`frame.to_ndarray` 后），不影响 H.264 解码链
- audio 不丢，queue buffer 住直到对齐点
- 对齐后 a/v 起点 = `max(a_first_pts, v_first_pts)`，后续即使各自本地时钟走也不会积累错位

### 实测数据（7/19 22:35）

```
[AV_ALIGN] audio 第一帧到达 emit, a_pts=0
[AV_ALIGN] ✅ 对齐！丢过 0 video emit, v_pts=1640, a_pts=0, diff=+1640ms
```

audio 第一帧到达时，video pts = 1640ms（video 已经在 server 里了），差 1640ms。这次没丢 video（emit 时 audio 还没到的判断路径未被触发），但**逻辑保证**后续任何情况都能对齐。

翀哥视觉确认："基本对上了 这个方法是有效的"。

## 文件改动

`engine/src/voice-chat/python/server.py`：
- 全局状态：`_av_aligned`, `_a_first_seen_ts`, `_v_dropped_before_align`
- `video_emit()`: 加对齐判断，未对齐返回 black frame
- `emit()` audio: 记 `_a_first_seen_ts`（第一次拿到 sdk_pts_ms）

## 注意事项

1. **重启后会重新对齐**：每次 server 重启 _av_aligned 重置，第一次连接都会走对齐流程
2. **冷启动 1.6s 延迟**：audio pull SDK 时序跟 video 不同步（1680ms），这是 SDK 端固有，对齐只是解决浏览器渲染不一致
3. **持久化方案**：如果换 aiortc 直接用 SDK pts，就不用这个闸门了（pts 自身就反映时序差）

## 后续可选优化

- **优化 1**：不丢 video 帧，而是 buffer 起来延迟放——对齐点取的是 a/v 都到的瞬间，所以 audio 第一帧到达时所有 video 帧都可以回放。但 audio 缓冲会更长，**取舍**。
- **优化 2**：直接用 SDK pts 替换 fastrtc 自算 pts（monkey-patch utils.py:249 和 tracks.py:705），不用闸门也能对齐。
- **优化 3**：换 aiortc 完全自己控制 pts（最大自由度，工作量也最大）。

当前方案已够用，明天回北京复现验证。