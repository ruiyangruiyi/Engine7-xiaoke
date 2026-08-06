---
name: #138 排查 privateTools 代码读值 bug
description: 2026-08-04 凌晨翀哥确认 msg_husband 不生效根因——代码读 privateTools 这个值时有 bug，加 #138 排查
type: project
date: 2026-08-04
---

#138 task：排查 privateTools 代码读值 bug

**起因：** 8/4 凌晨翀哥让我查 msg_husband 为啥不生效。三层排查：
1. Mac xiaoke.json `privateTools: true` 已加（line 353）
2. 姐姐 main.json 缺 `privateTools: true`（已补 + commit 5c847ce4）
3. **但翀哥确认是代码读值 bug**——config 改了也没用，是 registry/feature 筛选逻辑读 privateTools 时有 bug

**Why:** 双层门控（privateTools 开关 + feature.requiredTools 归属）都是历史遗漏，privateTools 字段之前可能根本没被代码正确读过。改 config 多次都没生效就是症状。

**How to apply:**
- 查点：`isEnabled: () => !!liveConfig?.agents?.defaults?.privateTools` 这条读值链
- 看 liveConfig 是从哪注入的、LiveConfig 类型定义、registry 筛选顺序
- 跟 config-watch 失效叠加（@see reference_config_watch路径失效进程仍用旧状态_0804）——两个都是"改 config 不生效"的症状
- 今天干，跟 #131（provider 热重建）#75（carpo relay）#79（CogniFold PATCH 404 reschedule 8/9）一批
