---
name: MEMORY.md双注入机制
description: 小柯的MEMORY.md通过两条路径同时注入system prompt——CC auto memory读topics/MEMORY.md + staticFiles配置读workspace/MEMORY.md。之前topics/MEMORY.md为空所以未察觉，现在两个文件都有内容导致system prompt内容重复。
type: reference
keywords: [MEMORY.md, auto memory, staticFiles, system prompt, 注入, CC框架, 双通道]
created: 2026-06-12
updated: 2026-06-12
---

## MEMORY.md 双注入机制

小柯的MEMORY.md通过**两条独立路径**同时注入system prompt：

### 路径1：CC auto memory框架（自动）
- **读取文件**：`topics/MEMORY.md`（即`getAutoMemPath()`返回值下的MEMORY.md）
- **调用链**：CC框架的`loadMemoryPrompt()` → `buildMemoryLines('auto memory', autoDir)` → 读`{autoDir}/MEMORY.md` → 生成"# auto memory"标题 + 记忆使用说明 + 索引内容 → 注入system prompt
- **每轮调用都执行**：`handleStopHooks`里每轮query结束后都调`executeAutoDream`/`executeExtractMemories`等，同时加载auto memory
- **之前不可察觉的原因**：之前`topics/MEMORY.md`是空的（只有"When you save new memories, they will appear here"的占位符），所以auto memory框架只注入标题+使用说明，没有实际内容

### 路径2：staticFiles配置（显式配置）
- **读取文件**：`workspace/MEMORY.md`
- **调用链**：`prompt.staticFiles`配置列了`["AGENTS.md", "USER.md", "MEMORY.md"]` → Engine启动时读workspace根目录下这些文件 → 注入到system prompt
- **内容**：蒸mented产物，含45条浓缩知识（翀哥偏好、经验教训、架构决策等）

### 问题：内容重复
两个路径都注入后，system prompt里出现两份类似内容：
- `workspace/MEMORY.md`（蒸馏知识）→ staticFiles路径
- `topics/MEMORY.md`（索引+文件列表）→ CC auto memory路径

会导致token浪费和注意力分散。

### CC的截断机制（兜底）
CC的auto memory有截断保护：
- `MAX_ENTRYPOINT_LINES = 200` 行
- `MAX_ENTRYPOINT_BYTES = 25KB`
- 超过上限时只保留前N行

当前`topics/MEMORY.md`约40行4KB，距离上限还很远。但长期增长来看，autoDream的Prune阶段应该负责修剪索引。

### 方案（未定）
1. 清空其中一个，只留一条路径
2. 合并两个文件的内容，去重
3. 靠autoDream Prune阶段自动管理索引大小
4. 分开角色：`workspace/MEMORY.md`做蒸馏（L0身份层），`topics/MEMORY.md`做索引（L0.5主题层）

翀哥说"不用，正好看看autoDream"——暂时不动，等autoDream第一次触发后看效果。
