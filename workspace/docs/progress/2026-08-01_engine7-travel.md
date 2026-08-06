# 2026-08-01 Progress

## 今日完成

### engine7 export/import 跨机器迁移（#129）— 从 7.1.8 修到 7.1.23
- **7.1.12** session 映射文件没打包
- **7.1.16** 76 个 cron session 全打包了（只保留主 session）
- **7.1.17** jsonl 文件路径没脱敏
- **7.1.18** JSON 里 `D:\\` 双反斜杠没替换
- **7.1.19** engine UUID 查错（platform session ID ≠ engine UUID）+ `\\` → `/`
- **Win→Mac→Win 全流程验证通过**：144 条消息 session restore，workspace/calendar/config 全量恢复
- 落盘 `docs/knowledge/engine7-travel-指南.md`

### 代码改动（push 到 twinsun-hearth）
- **prompt.ts** 运行时上下文简化：删掉冗余的 channel/频道ID/发送者ID（meta 里已有），只留当前时间 + section title（commit `4eb36d8c`）
- **cli-travel.ts** export 白名单排除 `calendar.db`（废弃文件，真正在用的是 `.calendar/calendar.db`）（commit `b40b69fa`）
- Mac SSH key 加到 GitHub，`twinsun-hearth` 代码双向同步

### 其他
- 删掉 `workspace/calendar.db`（老版本残留）
- 姐姐把 EverOS 接入 engine，OpenClaw memory core 即将退役（等导入 topics 记忆）
- Mac 上 import 后 skills 全量带过来（48 个）

## 关键经验
- travel 前 import 必须停 engine，否则 starting fresh 覆盖映射
- `~$` Office 临时文件会锁死 import（EPERM），export 时排除
- npm registry 同步有延迟，publish 后不要立刻 install

## 当前状态
- Mac engine 7.1.23 运行中，session 恢复正常
- Windows engine 待姐姐 EverOS 接入完成后重新编译
- 无待办任务
