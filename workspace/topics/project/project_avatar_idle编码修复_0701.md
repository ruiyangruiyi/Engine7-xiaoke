---
type: project
created: 2026-07-01
tags: [avatar, h264, ffmpeg, flashhead]
date: 2026-07-01
---

# Avatar idle 编码修复 (7/1)

## 问题
reload_avatar 生成 idle 用 cv2 VideoWriter(mp4v/mpeg4)，streamer 解不了。

## 修复（3个bug）
1. cv2 mp4v → ffmpeg pipe(libx264, Main profile, bframes=0, 静音AAC)
2. FlashHead Tensor → numpy(.cpu().numpy().astype(np.uint8))
3. capture_output → PIPE（AutoDL Python 兼容）

## 验证
- idle_25fps.mp4：h264 Main, 250帧, 10秒, 无B帧, AAC音频
- 切换到 xiaoke.jpg 成功，FlashHead 出图正常

## Commits
b9ababa fix: reload_avatar generates h264 idle_25fps.mp4
c62bf46 fix: convert FlashHead tensor to numpy
80e1091 fix: use PIPE instead of capture_output
