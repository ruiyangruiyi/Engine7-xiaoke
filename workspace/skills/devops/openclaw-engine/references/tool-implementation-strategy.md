# Tool实现策略 — 三条路线 (2026-05-27)

翀哥定方向：不要从零造轮子，基础tool必须"特别好用"。

## 三条路线

### 路线1：参考Claude Code TS源码（最优先）
- 同技术栈（TypeScript），直接可参考
- `@anthropic-ai/claude-code` npm包含完整TS源码
- GitHub解包: `github.com/pratikiitdh/claude-code-source-code`
- 精简版: `github.com/e10nMa2k/cc-mini`
- Claude Code 6个核心tool: Read/Write/Edit/Bash/Grep/Glob
- Edit的关键特性: replace_all、multi-edit、失败返回上下文片段辅助LLM修正

### 路线2：翻译Hermes Python代码（小柯帮翻）
- fuzzy_match 8策略 → TS版3-4策略 ~150行
- 安全防护检查 → ~50行
- 重复读循环检测 → ~30行
- 写后lint → ~40行

### 路线3：自建代码当baseline，不删
- 现有6个tool能跑能测，作为baseline保留
- 逐步用路线1+2替换handler实现
- schema和registry接口不变

## CC vs Hermes量化差距

| Tool | CC行数 | Hermes行数 | 差距 | 核心差距 |
|------|--------|-----------|------|---------|
| read | 55 | ~700 | 12x | 无重复读循环检测、无敏感脱敏、无相似文件推荐 |
| write | 38 | ~235 | 6x | 无安全路径保护、无写后lint检查 |
| edit | 55 | ~1300 | 24x | 无模糊匹配(最大差距)、无多文件编辑、无diff输出 |
| exec | 70 | ~2340 | 33x | 无后台进程、无安全扫描、无沙箱环境 |
| web_search | 63 | ~2600 | 41x | 单后端(Tavily)、无SSRF防护 |
| web_fetch | 71 | ~1500 | 21x | 无PDF支持、无批量URL、正则解析HTML |
| 总计 | 352 | ~8675 | 25x | |

## 各tool详细差距分析

### read.ts vs Hermes read_file
- **缺失**: 设备文件保护(/dev/zero等)、重复读取循环检测(≥3次警告≥4次阻断)、敏感内容脱敏、文件变化感知(mtime检查)、相似文件推荐、字符数限制(非字节)
- **建议**: 加设备文件黑名单 + 重复读计数 + 字符限制替代5MB字节限制

### write.ts vs Hermes write_file
- **缺失**: 敏感路径保护(/etc/,.ssh等)、写后lint检查(.py/.json等)、并发写保护(per-path锁)、跨agent写冲突检测
- **建议**: 加敏感路径黑名单 + 写后语法检查

### edit.ts vs Hermes patch (最大差距)
- **缺失**: 模糊匹配(8策略递进)、V4A多文件编辑、unified diff输出、未匹配时"Did you mean?"引导
- **Hermes fuzzy_match策略**: 精确→行trim→空白规范化→缩进弹性→转义规范化→边界trim→块锚定→上下文感知
- **建议最小实现**: 精确→逐行trim→normalize空白，3种策略就够

### exec.ts vs Hermes terminal
- **缺失**: 后台进程管理(start/poll/wait/kill)、PTY模式、环境隔离(Docker/SSH/Modal)、tirith安全扫描、进程完成通知、sudo密码管理
- **建议**: spawn替代exec(已改)、后台进程管理(P1)、安全扫描(P2)

### web-search.ts vs Hermes web_search
- **缺失**: 多后端(7种)、SSRF防护(url_safety.py 327行)、LLM辅助总结、网站访问策略
- **建议**: 加URL安全检查(阻止内网/元数据endpoint) + 多后端支持

### web-fetch.ts vs Hermes web_extract
- **缺失**: PDF支持、批量URL(最多5个并行)、cheerio替代正则解析HTML、LLM长内容总结、2M大页面拒绝
- **建议**: 加PDF检测 + 批量URL + SSRF防护

## 执行优先级

1. 🔴 edit模糊匹配（LLM编辑成功率60%→90%）
2. 🔴 read/write安全防护（防agent搞崩系统）
3. 🔴 重复读循环检测（防LLM死循环浪费token）
4. 🟡 写后lint检查
5. 🟡 web_fetch PDF+批量
6. ⚪ 后台进程管理
7. ⚪ JSON结构化输出
