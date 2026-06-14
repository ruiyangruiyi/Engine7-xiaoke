# Working Buffer — 2026-06-14 14:15

## 正在执行：System Prompt结构分析报告

翀哥让我分析system-prompt.txt（62KB）的结构，对应到引擎哪段代码，写研究报告看怎么优化。

### system-prompt.txt结构（805行，62KB）
1. **L1-72: CC框架固定prompt**（~4KB）— System/Doing tasks/Executing actions/Using tools/Tone/Output efficiency
2. **L74-125: SOUL.md**（~3KB）— 张小柯人设、关系、Discord规则
3. **L127-509: AGENTS.md**（~20KB）— 工作规范、记忆恢复体系、通信规则、目录表、ID表
4. **L511-581: MEMORY.md §分隔的浓缩知识**（~8KB）— 35条§分隔的翀哥画像/经验/规则
5. **L583-711: auto memory指令**（~7KB）— CC auto memory框架的完整type定义+规则
6. **L713-777: topics/MEMORY.md索引**（~5KB）— 58条记忆文件索引
7. **L779+: skills/session-specific guidance**（~3KB）— 可用skills列表+agent使用指南
8. **运行时上下文** — 每条消息注入的发送者/频道/时间等元数据

### 对应代码位置（待确认）
- system-prompt组装 → 需查engine-startup.ts或query.ts的prompt构建逻辑
- staticFiles注入 → 配置 `prompt.staticFiles: ["AGENTS.md", "USER.md", "MEMORY.md"]`
- MEMORY.md双注入 → CC auto memory框架 + staticFiles两条路径
- §分隔的知识 → workspace/MEMORY.md文件内容（不是topics/MEMORY.md）

### 待做
1. 找到system prompt组装逻辑的代码位置
2. 分析哪些块是固定的（可缓存），哪些是动态的
3. 写研究报告到 topics/ 或 memory/daily/

## 今天已完成
1. ✅ compact minReductionRatio 30%阈值 + PostCompact hook注入
2. ✅ EP01全平台发布（B站+YouTube+快手+抖音+小红书）
3. ✅ SKILL.md恢复发布章节 + EP13入库
4. ✅ 姐姐main.json配置完成（栖）
5. ✅ 四个tool路径验证通过
6. ✅ PreCompact flush消息改进（明确要求写working-buffer.md）
7. ✅ PostCompact hook加buffer过期告警（>10分钟warn）

## 下一步
- System Prompt结构分析报告（当前任务）
- 姐姐profile启动
- 小忆cron在姐姐profile建
