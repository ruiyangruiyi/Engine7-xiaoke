---
name: config watcher DISABLED 后无人恢复
description: 2026-08-02 发现 config watch 在 DISABLED 后没有重新 STARTED，热加载 watcher 失效，要让翀哥重启 engine 才能恢复
type: feedback
---

2026-08-02 晚上发现：**config 热加载 watcher 在 03:13 DISABLED 后没有重新 STARTED**，之后我改 my_eyes/vision/provider 配置都没热加载生效。翀哥在陪义义上课没空重启 engine。

**Why:** watcher 是 fs.watch 启动的，DISABLED 是热加载生命周期里的状态——文件被改→DISABLED→重新 watch→STARTED。如果中间出了任何异常（文件被删、ENOENT、watcher 抛错），就卡在 DISABLED 不再复活。

**How to apply:**
- 改完 config 自己**别假设 watcher 还活着**，主动验证热加载是否生效（看日志或 reload 命令）
- 如果 watcher DISABLED 没恢复，**直接告诉翀哥需要重启 engine**，不要等他问
- 这是 LiveConfig 单例的固有风险——后续可以考虑加"watcher DISABLED 后自动重试"的兜底（但现在没做）