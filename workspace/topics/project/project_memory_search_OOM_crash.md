---
name: memory_search OOM crash修复
description: 6/15姐姐memory_search触发session sync，9289个旧session文件爆4GB heap→归档+500上限+sync开关
type: project
---

# memory_search OOM Crash — 2026-06-15

## 问题
姐姐调用memory_search时crash，日志：
```
listSessionFilesForAgent: found 9289 session files
FATAL ERROR: Reached heap limit - JavaScript heap out of memory
```

## 根因
姐姐从OpenClaw搬来时，`agents/main/sessions` 目录继承了9289个旧session JSONL文件（共18,404个文件）。`memory_search` 触发session sync时，`listSessionFilesForAgent` 全量加载索引，4GB堆爆。

## 修复（四步）
1. **归档旧session文件** ✅ — 18K+文件搬入 `_archive`（翀哥执行powershell脚本）
2. **session sync加500上限** ✅ — `manager-sync-ops.ts` 加 `SESSION_SYNC_LIMIT = 500`，超了打warning不崩
3. **sync.enabled开关（第一次：类型过滤失效）** ⚠️ — 初始用 `this.settings.sync.enabled === false`，但 `ResolvedMemorySearchConfig` 类型定义里没有 `enabled` 字段，JSON解析时被吞掉了，guard不生效
4. **sync.enabled开关（第二次：裸读原始config）** ✅ — 改用 `isSyncDisabled(this.cfg)` 直接读 `cfg.agents.defaults.memorySearch.sync.enabled`，绕过类型过滤

### 四个入口加guard：
- `ensureWatcher`
- `ensureSessionListener`  
- `ensureSessionStartupCatchup`
- `ensureIntervalSync`

### 漏网路径：`startAsyncSearchSync`
`memory_search` 调用时走 `startAsyncSearchSync`，它的 `enabled` 参数检查的是 `onSearch` 配置，不是我们的 `sync.enabled`。在dist中patch了该路径（注入syncDisabled参数直接读原始config）。13:34完成patch，重启后触发路径已被堵→log确认无sync相关输出 ✅

### 副作用
sync关掉后，ollama bge-m3 embedding限流日志 `memory embeddings rate limited; retrying in xxxms` 仍在出现——这是embedding批处理的失败重试延迟（ollama只试1次就进退避），不是真限流。后经排查 `startAsyncSearchSync` 漏网路径已补，重启后消失。

### 经验教训
1. **改代码必须改src源码，改dist没意义** — 翀哥纠正。虽然dist改起来快，但会丢失（recompile后覆盖），架构上不可持续。
2. **配置开关要考虑config类型定义可能过滤未知字段** — 第一次用 `this.settings.sync.enabled` 被 `ResolvedMemorySearchConfig` 类型定义吞掉（没有enabled字段）。第二次改用 `this.cfg.agents.defaults.memorySearch.sync.enabled` 裸读原始config才生效。
3. **sync清理逻辑bug：文件消失就删DB+vector** — `syncSessionFiles` 的清理逻辑（line 1074-1100）在跑完当前文件后，遍历DB里的files表——任何不在当前目录里的文件，连files条目+vector+chunks+FTS一并删除。所以文件搬进 `_archive` → vector库清空 → 搬回来时全不认识了，重索引。
   
   正确做法：文件不在目录时保留DB记录只打warn，搬回来时mtime/size没变就跳过重索引。这个修好后恢复历史session就是两步：restore-sessions.ps1搬回来→开sync增量索引。

## 配置
```
"memorySearch": {
  "sync": { "enabled": false }  // 不配→默认启用；false→全部禁用
}
```
姐姐main.json加此项，重启后生效。小柯不变（默认启用）。

## 后续
- 归档后向量库session embedding指向旧文件→memory_search报embedding/provider error
- 已从main.json sources中移除 `sessions`，只留 `memory`（memdir路径）
- 翀哥有restore-sessions.ps1脚本可恢复最近500个活跃session文件
- 恢复前需要：sync关掉→搬回文件→确认memory.db embedding可用→sync开+加回sessions源

## 关联
- 旧session来自OpenClaw搬家遗留，跟 `project_姐姐搬新家.md` 关联
