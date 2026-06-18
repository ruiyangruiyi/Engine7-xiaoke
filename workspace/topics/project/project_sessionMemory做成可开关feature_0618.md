---
name: sessionMemory 做成可开关 feature
description: 6/18 15:47翀哥拍板B方案——sessionMemory写死true改为可配置feature开关，设false
type: project
---
6/18 15:47 翀哥观察日志发现 topic-recall/extract 关了后 sessionMemory 还在跑。

"按说这个也要做成开关 这个其实平常没啥用 也消耗资源"。

15:50 翀哥拍板做B方案："干不了大活先把小活清理了"。

**实施（15:50-15:52）：**
1. loader.ts `FeatureConfig` 加 `session-memory?: boolean` + 默认值 true
2. xiaoke.json 加 `"session-memory": false`
3. sessionMemory.ts `isSessionMemoryEnabled()` 读 config.features
4. engine-startup.ts `initSessionMemory` 传 features 参数
5. rebuild 完成 + 翀哥重启 ✅

**当前状态：**
- topic-extract: false
- topic-recall: false
- session-memory: false
- topics（死开关）：已从 loader.ts 和 xiaoke.json 删掉

**下一步（16:00-16:18 命令层折腾）：**
- 最终实现：3个slash command `/topic-recall` `/topic-extract` `/session-memory`，可选参数 `state: on|off`
- 无参数=查状态，有参数=切换+持久化（写回 xiaoke.json）
- Runtime 改 `deps.features` + `config.features` 即时生效
- 同步写回 xiaoke.json 磁盘持久化（写 `cfg.agents[0].features`）
- 中间绕了弯路：6独立命令(recall-on/off等)→toggle→只查不改→最终回归参数形式
- **翀哥反复纠正"按需求做不要改设计"**——他要的是 3命令+参数 形式最初就说清楚了

**踩坑（16:22-16:30 磁盘写路径修）：**
- 我第一版磁盘写用了 `cfg.profile.features`，但 engine 实际读的是 `cfg.agents[0].features`（L287）
- xiaoke.json 有两个 features 块：`agents[0].features`（实际生效）和 `profile.features`（无用残留）
- 16:28 翀哥让删掉无用的 `profile.features` 块+代码里的那条路径
- 最终：只写 `cfg.agents[0].features`，干净了
