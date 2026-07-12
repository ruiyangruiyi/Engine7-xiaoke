# aim: 实现引擎层 Nudge 机制

## 目标
1. session-history.ts 从 inner-voice/ 搬到 src/session/，所有现有 import 仍工作
2. src/nudge.ts 实现：per task 状态、L1 时间维度、6 种 NudgeAction
3. engine 启动时 nudge 正常加载（日志输出 `[nudge] Started`）
4. 实际验证：构造 - [~] 任务静止 5 分钟，能看到 nudge 注入 main session

## 元信息
- 频道: feishu（自己的 session，无协作者）
- 指派: 小柯自己
- 创建时间: 2026-06-30 18:43
- 检查间隔: 10min
- 状态: 🔄 进行中

## 进度记录
- 2026-06-30 18:43 创建 aim，拆任务（7 步）
- 2026-06-30 18:46 session-history.ts 抽离完成（src/session/session-history.ts + inner-voice 兼容 re-export）
- 2026-06-30 18:48 src/nudge.ts 实现完成（416 行，超出预期 200 行但覆盖了全部 L1 + L2 钩子）
- 2026-06-30 18:48 config.nudge 配置加载完成
- 2026-06-30 18:50 注册到 engine-startup 完成（start + mainQueryRunning 联动）
- 2026-06-30 18:50 小柯 workspace prompts/nudge-prompt.md 准备完成
- 2026-06-30 18:50 esbuild 构建通过（dist/main.mjs 6.1MB）
- 待翀哥重启验证启动日志
- 待实际跑一遍（构造 - [~] 任务静止 5 分钟）