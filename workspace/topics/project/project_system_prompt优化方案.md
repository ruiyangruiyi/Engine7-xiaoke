---
name: System Prompt优化方案（已部署）
description: 6/14完成——BLOCK_REGISTRY框架 + order自定义 + prompts文件覆盖机制 + 小柯/姐姐各profile精简版（已重启生效）
type: project
---

## ✅ 已完成并部署（6/14重启生效）

### 核心架构：BLOCK_REGISTRY

- 11个block注册为积木：intro/system/doing-tasks/actions/using-tools/tone-style/output-efficiency/soul/static-files/memory-instructions/boundary
- `buildStandardPrompt()` — 固定顺序，新人开箱即用
- `buildCustomPrompt()` — 支持order（自定义顺序）+ exclude（排除block）
- order内支持文件名（如`"AGENTS.md"`）作为独立项，可插在任何位置

### 文件覆盖机制（方案B）

- `workspace/prompts/{block-name}.md` 存在则覆盖默认函数内容
- 小柯：system/doing-tasks/output-efficiency/actions 四个覆盖文件（6.2KB→2.6KB，省58%）
- using-tools保持原样（翀哥说不用改）
- 后来也扩展到extract和memory-instructions

### 三个profile配置

**小柯xiaoke.json：**
```
soul → AGENTS.md → system → doing-tasks → using-tools → output-efficiency → actions → USER.md → MEMORY.md → memory-instructions
```
- 砍了intro（"不是助手是人"）和tone-style
- soul放在最前面（翀哥要求，人格先行）
- AGENTS.md紧接soul后（翀哥要求："工作方式后面，AGENTS.md接在soul后面"）
- 砍了static-files block（order内已单独列文件名，staticFiles与order互斥）

**姐姐main.json：**
- 同上去掉actions（翀哥说姐姐不需要actions block）
- 只需using-tools（秀tool用）

**standard模式（新人）：**
- 默认11个block全量加载

### MEMORY.md索引不再每轮注入

- 通过`prompts/memory-instructions.md`覆盖`buildMemoryPrompt()`
- 只保留1KB行为指令（怎么存、什么时候存、4种type）
- 砍掉67行10KB索引目录（省16KB）
- topics/下的文件一个没删，memory_search照样能搜到
- **Why:** 翀哥发现后问"这个10KB索引值不值得每轮加载"，讨论后决定直接砍索引。翀哥认为MMEORY.md索引有了也不一定回去读，真正驱动记忆注入的是recall机制

### 配置方式变迁

1. 最初：只用staticFiles批量注入
2. 第一版：order列表控制block顺序 + exclude排除
3. 最终方案：order与staticFiles互斥（翀哥要求逻辑干净），配了order就忽略staticFiles

### 代码改动

- `src/prompt.ts` — BLOCK_REGISTRY + buildStandardPrompt + buildCustomPrompt
- workspace/prompts/ — 各profile独立覆盖文件

### 后续待办（翀哥列）

1. 定制emotion extract/recall提示词（参考姐姐cron）
2. topics/MEMORY.md对extract/autoDream逻辑的影响检查
3. 外面MEMORY.md（Hermes蒸馏）搬过来，闭环（等姐姐搬家后做）
