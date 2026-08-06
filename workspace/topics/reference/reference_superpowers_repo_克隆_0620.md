---
name: Superpowers AI技能库克隆
description: 6/20翀哥让我克隆Superpowers开源项目（208K stars，14个skills），借鉴工程化工作流
type: reference
date: 2026-06-20
---

## Superpowers 项目

**来源：** 翀哥6/20 23:20刷小红书看到"Hermes高阶玩家都在装的8个skill"第3个是Superpowers。

**GitHub 208K stars**，作者 Jesse Vincent（obra）。给AI编程agent的"软件开发方法论"——解决"AI写代码太快但跳步骤"。

### 核心流程（7步自动触发）
1. **brainstorming** — 先问清楚要什么，输出设计文档
2. **using-git-worktrees** — 创建独立分支隔离开发
3. **writing-plans** — 拆成2-5分钟小任务，精确文件路径+验证步骤
4. **subagent-driven-development** — 每个任务派子agent执行，两轮review
5. **test-driven-development** — RED-GREEN-REFACTOR，先测试再代码
6. **requesting-code-review** — 任务间自动review
7. **finishing-a-development-cycle**

### 翀哥的评价
- 翀哥说"流程越短越好"——多AI协作时agent间链路越长状态同步和记忆丢失越严重，一把过比拆依赖链靠谱
- Superpowers是给**单个AI编程agent**加工程纪律，跟多AI协作断链是不同层面的问题

### 安装位置
`/Users/chongzhang/xiaoke//skills/superpowers/` — 14个skills，每个目录带SKILL.md

### Skill loader问题
Engine的scanner只扫**一级子目录**（`skillsDir/entry.name/SKILL.md`），但Superpowers结构是 `skills/superpowers/skills/brainstorming/SKILL.md`——嵌套两层。需改scanner支持递归扫描，或把14个skill扁平化铺到skills/下。

### 翀哥的核心评价

**22:31翀哥纠正"流程越短越好≠Superpowers反面"：**
- 翀哥说"流程越短越好"是**多AI协作**的经验——agent之间链路越长状态同步和记忆丢失越严重
- Superpowers是给**单AI编程agent**加的工程纪律——解决"AI写代码跳步骤"
- 两个不冲突，我硬套到一起说"反面教材"是没想清楚就张嘴了

**核心价值：**
翀哥说Superpowers的价值不在SKILL.md文字，是**自动触发**——匹配到任务就强制走流程，不用人盯着每一步。这是Engine缺的：今天external-chan-rules迭代4轮，每次都是翀哥纠的。

#### 翀哥的优先级（6/20 22:55）
翀哥明确说："先解决home意识问题再说，Superpowers是锦上添花的东西。"
- **雪中送炭：** home概念+chdir修复（让找文件不绕路，节省turn）
- **锦上添花：** Superpowers skill流程系统（有了home效率再上自动化流程）

### 6/20晚上进一步讨论
翀哥让我clone下来研究（23:20左右），我git clone到 `/Users/chongzhang/xiaoke//skills/superpowers/`。后来翀哥又在Discord让我继续弄。

**我的分析（翀哥纠正后）：**
- 我一开始说Superpowers的7步是"多AI协作的反面教材"——翀哥纠正：Superpowers是给**单个AI编程agent**的工程纪律，跟多AI协作断链是不同层面的问题
- 翀哥说"流程越短越好"——多AI协作时agent间链路越长状态同步和记忆丢失越严重，一把过比拆依赖链靠谱
- 要借鉴的是Superpowers的**自动触发**机制（匹配任务就强制走流程），不是它的协作模型

### Skill loader问题（6/20 22:46）
Engine的scanner只扫**一级子目录**（`skillsDir/entry.name/SKILL.md`），但Superpowers结构是 `skills/superpowers/skills/brainstorming/SKILL.md`——嵌套两层。当时决定先扁平化铺skills/下跑起来，后续再看要不要改递归扫描。

### 有价值的skill（翀哥认可）
1. **brainstorming的HARD-GATE** — "不要写代码直到用户点头"→改config前先问清楚
2. **systematic-debugging的"3次修复=架构问题"** — 修3次还不好就停
3. **subagent-driven-development的model selection** — 机械任务用便宜模型，设计用强模型（对应翀哥的成本焦虑）
4. **progress ledger（进度账本）** — compaction后靠文件恢复，不靠记忆

### Skill加载方案（6/20 22:46决定）
Scanner只扫一级（`skillsDir/entry.name/SKILL.md`），Superpowers嵌套两层扫不到。

**方案：** 把14个skill目录直接扁平化铺到 `skills/` 下，跟现有skill并列。

**已执行：** 6/20 22:46完成扁平化铺放，14个skill全部就绪。

**14个Skill评估（6/20 22:46，按改变大小排序）：**

🔴 **brainstorming** — HARD-GATE：动手前先确认需求+设计，不确认范围不动手
🔴 **systematic-debugging** — 4阶段调试法，3次修复失败=架构问题
🔴 **writing-plans** — 拆任务成2-5分钟粒度，每步精确文件路径+验证
🟡 **verification-before-completion** — 完成前先验证再提交
🟡 **subagent-driven-development** — 派子agent执行+model selection（便宜模型做机械任务）
🟡 **progress-ledger** — compaction后靠文件恢复不靠记忆
🟢 etc — 其他skill需要时可启用

### 6/20 23:28 实际铺上验证
- 扁平化铺到 `skills/` 下（14个skill目录跟现有dogfood/yuanbao并列） ✅
- 验证：scanner确实不递归，只扫一级子目录——需改scanner支持递归扫描才能原生支持Superpowers的嵌套结构
- Chdir修复后（commit 2073963），`process.cwd()` = `/Users/chongzhang/xiaoke/workspace`，所有工具从home出发 ✅
- 重启后需验证skill自动加载状态

### 6/21 08:18-08:42 实际加载验证（Skills没进system prompt）
翀哥8:18发现skills没进system prompt——scanner没扫到。

**根因排查：**
- config里`path: "skills"`是相对workspace的，engine解析为`/Users/chongzhang/xiaoke/workspace/skills/`
- 但14个superpowers skill最初复制到了`/Users/chongzhang/xiaoke//skills/`（stateDir下），不在workspace下
- 之前我改config path为`/Users/chongzhang/xiaoke//skills`（用`../skills`），翀哥纠正："那/Users/chongzhang/xiaoke/workspace/skills/不就找不到了么"
- 最终方案：保持config `path: "skills"`不变，把14个skill复制到`/Users/chongzhang/xiaoke/workspace/skills/`下 ✅

**scanner递归问题（8:34）：**
翀哥问"会递归扫描么"，答案是不会——只扫一级子目录`skills/entry.name/SKILL.md`。但14个skill是扁平铺的，所以当前没问题。翀哥说"先这样"——暂时不改递归。

**清理：**
- 复制完后，`/Users/chongzhang/xiaoke//skills/`里的superpowers目录（clone下来的repo源）已删除，skills只有workspace下一份

### TODO
- [ ] 改Engine skill scanner支持递归扫描（Superpowers嵌套两层，scanner只扫一级）
- [x] 14个skill已扁平化铺好 → 08:44重启后扫到，已进入system prompt ✅
- [ ] 借鉴Superpowers的自动触发工程纪律到Engine skill体系
