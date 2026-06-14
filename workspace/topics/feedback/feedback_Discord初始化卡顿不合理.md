---
name: Discord初始化卡顿与串行启动问题
description: 翀哥6/12晚反馈Discord重启卡好几分钟，飞书虽可初始化但"一直不能初始化完成"不合理
type: feedback
---

Discord登录初始化和启动流程存在性能/可靠性问题，已修复：

**现象（6/12晚22:39）**：
- **Discord**：重启后卡好几分钟（LOGIN_TIMEOUT重试5次 × timeout=15s + 指数退避 ≈ 2分半）
- **飞书**：虽然日志显示`Feishu adapter loaded`但Discord卡住时飞书也在等

**根因**：`startAll()`是串行连接 (`for...await`)，Discord卡LOGIN_TIMEOUT时飞书排后面干等

**修复（两阶段）**：

1. **第一阶段**：`startAll`从串行改为`Promise.allSettled`并行启动，各adapter互不阻塞
2. **第二阶段**（翀哥追问后优化）：`startAll()`改为**同步方法**，注册连接回调后立即返回，不再返回Promise。调用侧去掉`await`。连接在后台异步进行，谁先连好谁先可用。

**翀哥后续追问**（关键设计约束）：
- 飞书卡了会影响别人吗？→ 不会，并行启动互不影响
- 如果两个都卡了会影响后面吗？→ 同步startAll不阻塞，卡住的adapter自己重试，可视化/cron等后续初始化继续执行
- 最终约束：**启动流程不应被任何adapter的连接阻塞**，连接是异步后台行为

**Why:** 翀哥期望的启动体验是快速顺畅完成初始化，一个adapter网络抽风不应拖慢全局启动。后续可视化transport、cron等初始化也不应被adapter连接阻塞。

**How to apply:** 启动流程完全异步+并行，adapter之间完全解耦。连接不在启动时序关键路径上——谁先连好谁先可用，一个卡住不影响其他任何初始化。
