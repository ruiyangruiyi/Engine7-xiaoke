# Config Watcher 排查记录

**日期**: 2026-07-28
**问题**: startConfigWatcher 加了但改 config 文件后 reload 不触发

## 现象

- a30595ad 加了 fs.watch watcher
- src/dist 里都有 startConfigWatcher 代码
- engine 启动后日志里**没有** `[config-watch] watching` 输出
- 改 config 文件后 doReloadConfig 没被调用

## 排查步骤

### 1. console.log 不进日志文件 ✅ 已确认
- start.cmd 用 `node dist/main.mjs` 启动，stdout/stderr 没重定向
- engine 日志文件由内部 logger 写，console.log 只输出到终端
- 所以"[config-watch] watching"可能输出了但我们看不到

### 2. 加文件日志追踪
- commit `fa2e1a4a`: 在 startConfigWatcher 里加 `fs.appendFileSync` 写到 `stateDir/logs/engine-config-watch.log`
- 记录：STARTED / DISABLED / CHANGE / ERROR / RELOAD DONE
- **等翀哥重启后查看**

### 3. 可能的根因（待验证）
- **fs.watch Windows 兼容性问题**：Windows 上 fs.watch 对某些路径/编辑器不灵（VSCode 保存可能触发 rename 而不是 change）
- **_configFilePath 路径不对**：loadConfig 设的路径可能是相对路径，fs.watch 需要绝对路径
- **watcher 启动时报错被吞**：虽然 watcher.on('error') 有处理，但 console.error 也不进日志

## 验证方法

翀哥重启后：
1. 立刻看 `/Users/chongzhang/xiaoke//logs/engine-config-watch.log` —— 有 STARTED 说明 watcher 启动了
2. 改 config 文件 —— 看 CHANGE + RELOAD DONE 日志
3. 调 service tool —— 看新 service 是否出现
