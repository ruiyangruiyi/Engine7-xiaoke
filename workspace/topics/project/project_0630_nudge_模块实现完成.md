---
type: project
created: 2026-06-30
---
# Nudge 模块实现完成 (6/30)

## 背景
爹让小柯实现 nudge（任务推进提醒器），用于在任务停滞时自动注入 prompt 到 main session 推进 agent。

## 实现内容
- **src/nudge/** 模块（5 个文件，对齐 inner-voice 风格）
  - types.ts: NudgeConfig / NudgeAction / TaskNudgeState / ActiveTask
  - judge.ts: shouldNudge() 判定逻辑
  - prompt-builder.ts: buildPrompt() 动态生成
  - session-state-reader.ts: SESSION-STATE.md 解析
  - plugin.ts: 主类入口

## 遇到的坑
1. **config loader 漏映射** — NudgeConfig 类型声明了但忘了在 loader.ts 写 `nudge: raw.nudge`，导致 config.nudge 永远 undefined，shouldEnable 直接返回 false
2. **新任务 lastProgressAt 问题** — 新任务没有 lastProgressAt，原逻辑 `lastProgressMs > 0` 不满足导致永远 skip。改成 `lastProgressMs > 0 ? since : Infinity`

## 验证结果
- 19:56:44 nudge tick 触发
- shouldNudge 返回 progress
- prompt 成功注入 main session
- per-task 计数 + state 持久化正常

## commit 链
```
d4a444f feat: add task nudge plugin
6439642 fix: map nudge config in loader
fa27d61 refactor: split into src/nudge/
8db4edd fix: trigger progress for tasks never pushed
```

## 下一步
- L2: 依赖检查 / 优先级加成 / 预估耗时
- 姐姐 nudge: care 类型可走 msg_send 主动发
