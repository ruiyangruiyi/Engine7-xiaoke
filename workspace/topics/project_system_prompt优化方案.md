---
name: System Prompt结构分析与优化方案
description: 62KB system prompt的逐块拆解、代码对应、token成本计算、优化建议（2026-06-14）
type: project
---

# System Prompt 结构分析与优化方案

> 分析时间：2026-06-14 | 总大小：62,770 bytes (~62KB) | 来源文件：system-prompt.txt
> **6/14已全部实施完成**：BLOCK_REGISTRY (11 blocks) → `buildStandardPrompt()`/`buildCustomPrompt()` → 两个profile配置（order自定义+砍intro/tone-style） → order内支持文件名（AGENTS.md提前到soul后） → **staticFiles与order互斥** → **方案B文件覆盖机制**（workspace/prompts/{block-name}.md覆盖默认） → 小柯prompts精简版（system/doing-tasks/output-efficiency/actions四个文件，从6.2KB→2.6KB，省58%）→ **MEMORY.md索引不再每轮注入**（prompts/memory-instructions.md覆盖，只保留1KB行为指令，砍掉10KB索引，省16KB）。→ **姐姐也用同样的精简模式**（order里CC段只剩using-tools，其余去掉，不需要额外prompts覆盖文件）。全部已提交并重启生效 ✅

**后续待办（6/14翀哥确认）：**
1. emotion type + Milestone/Surprising Filter 定制extract提示词 — ✅ extract文件覆盖机制已实现（workspace/prompts/extract.md），小柯和姐姐的定制版已写好
2. 检查topics/MEMORY.md对extract/autoDream逻辑的影响 — ✅ 已检查，extract会继续往MEMORY.md追加索引（死数据），autoDream会读写修剪索引。不致命但需后续处理
3. Hermes蒸馏逻辑搬过来（等姐姐搬家后做）
4. emotion类型代码改动（memoryTypes.ts加emotion + extractPrompts.ts加双Filter + topics.emotion配置开关）— 方案已确认，待实施

## 一、逐块拆解（函数级精确对应）

system prompt由 `buildStablePrompt()` + `buildDynamicPrompt()` 两阶段组装（`src/prompt.ts`）。每个块精确对应一个代码函数 + system-prompt.txt的行号区间。

### Stable Prompt — CC框架层（7个硬编码函数，verbatim移植CC）

| # | 函数名 | prompt.ts | system-prompt.txt | 字节数 | 内容摘要 |
|---|--------|-----------|-------------------|--------|----------|
| 1a | `getIntroSection()` | L82-89 | L2-5 | ~0.8KB | agent自我介绍 + CYBER_RISK_INSTRUCTION(安全测试边界) + URL生成禁令 |
| 1b | `getSystemSection()` | L96-108 | L7-13 | ~0.9KB | # System：输出规则、权限模式、`<system-reminder>`标签、hooks说明、compaction说明。内部调用 `getHooksSection()`(L91-94) |
| 1c | `getDoingTasksSection()` | L110-138 | L15-29 | ~2.2KB | # Doing tasks：软件工程任务定义、先读再改、不过度设计(3条codeStyle)、不加多余错误处理(1条)、不创建helpers(1条)、安全编码、AskUserQuestion场景 |
| 1d | `getActionsSection()` | L140-153 | L31-41 | ~1.6KB | # Executing actions：危险操作确认规则——破坏性/不可逆/影响他人三类示例 + measure twice cut once原则 |
| 1e | `getUsingYourToolsSection()` | L155-180 | L43-52 | ~1.0KB | # Using your tools：不用exec替代read/edit/write/glob/grep + TaskCreate工具使用 + 并行tool call规则 |
| 1f | `getToneAndStyleSection()` | L216-227 | L54-59 | ~0.5KB | # Tone and style：不用emoji、简洁、file_path:line_number引用、不用冒号引出tool call |
| 1g | `getOutputEfficiencySection()` | L229-243 | L61-72 | ~0.5KB | # Output efficiency：直奔主题、输出聚焦决策/状态/错误三类 |
| | **CC框架合计** | | **L2-72** | **~7.5KB** | 7个函数按顺序 `parts.push()`，verbatim from CC `src/constants/prompts.ts` |

### Stable Prompt — OpenClaw叠加层（文件读取 + 代码生成）

| # | 来源 | 代码位置 | system-prompt.txt | 字节数 | 内容摘要 |
|---|------|----------|-------------------|--------|----------|
| 2 | `SOUL.md` 文件读取 | `prompt.ts:287-289` `readFileIfExists(path.join(workspace,'SOUL.md'))` | L74-125 | 2.2KB | 张小柯人设：身份、名字、关系、底线、Discord礼仪、常用ID |
| 3 | `AGENTS.md` staticFiles | `prompt.ts:293-301` staticFiles循环第1轮 | L127-509 | 12.6KB | 工作规范：铁律、记忆恢复体系、防循环、通信规则、目录表、互动原则 |
| 4 | `USER.md` staticFiles | 同上第2轮 | (合并入AGENTS区间附近) | 3.6KB | 翀哥用户画像（C/C++主语言、偏好、脾气等） |
| 5 | `MEMORY.md` staticFiles | 同上第3轮 | L511-581 | 8.3KB | §分隔的浓缩知识（翀哥画像/经验/规则/里程碑，36条§） |
| 6 | auto memory指令 | `prompt.ts:307-317` → `memdir.ts:175-205` `buildMemoryPrompt()` 内部调用 `buildMemoryLines()` | L583-711 | ~7KB | CC auto memory完整框架：4种type定义(user/feedback/project/reference)+when_to_save+how_to_save+what_not_to_save+frontmatter示例 |
| 7 | `topics/MEMORY.md` | `memdir.ts:181-186` `readFileSync(memoryDir/MEMORY.md)` → `truncateEntrypointContent()` 截断(200行/25KB上限) | L713-777 | 9.6KB | 58条记忆文件索引（- [Title](file.md) — hook格式） |
| — | boundary标记 | `prompt.ts:322` `parts.push(SYSTEM_PROMPT_DYNAMIC_BOUNDARY)` | L778附近 | <1B | `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` 分隔static/dynamic |
| | **Stable合计** | | | **~50KB** | 占总量80% |

### Dynamic Prompt（每turn可能变化）

| # | 函数名 | prompt.ts | 字节数 | 内容摘要 |
|---|--------|-----------|--------|----------|
| 8 | `formatSkillsListingForPrompt()` | L388-394 → 读SkillTool.prompt字段 | ~1KB | 可用skills列表（docx/dogfood/pdf/pptx/xlsx/yuanbao） |
| 9 | `getSessionSpecificGuidanceSection()` | L187-214 → 内部调用 `getAgentToolSection()`(L182-185) | ~1KB | Agent使用指南：Explore/Plan agent场景、简单搜索直接glob/grep、skill调用规则 |
| 10 | `getEnvInfoSection()` | L247-262 | ~0.5KB | # Environment：workspace路径、git状态、平台、shell、OS版本 |
| 11 | 运行时上下文（inline） | `prompt.ts:364-380` 拼接contextParts | ~0.5KB | 当前时间、平台、来源channel、消息类型、频道ID、发送者ID/名称、消息ID、sessionID |
| | **Dynamic合计** | | **~3KB** | |

### 总计：~53KB内容 + `\n\n` join格式化开销 ≈ 62KB

> **join开销约9KB**：`buildStablePrompt` 中每个 `parts.push()` 之间用 `\n\n` 分隔，多段拼接累计约2KB；`buildSystemPrompt` 合并stable+dynamic再加 `\n\n`。实际测量system-prompt.txt 62.7KB - 源文件36.4KB(SOUL+AGENTS+USER+MEMORY+topics/MEMORY) - CC框架~7.5KB - auto memory指令~7KB ≈ 11.8KB为格式化/markdown结构/join开销。

## 二、组装流程（代码级）

```
buildStablePrompt(workspace, staticFiles)
  ├─ CC Static Sections (硬编码，verbatim from CC)
  │   ├─ getIntroSection()          # L1-88ish
  │   ├─ getSystemSection()         # hooks/tabs/tags/compaction说明
  │   ├─ getDoingTasksSection()     # 不加feature/不过度设计等规则
  │   ├─ getActionsSection()        # 危险操作确认规则
  │   ├─ getUsingYourToolsSection() # 用read不用cat等
  │   ├─ getToneAndStyleSection()   # 简洁/不用emoji
  │   └─ getOutputEfficiencySection()
  │
  ├─ OpenClaw叠加层
  │   ├─ SOUL.md                     # 人格/身份
  │   ├─ staticFiles循环             # AGENTS.md + USER.md + MEMORY.md
  │   └─ memdir.buildMemoryPrompt()  # auto memory指令 + topics/MEMORY.md内容
  │
  └─ SYSTEM_PROMPT_DYNAMIC_BOUNDARY   # 分界标记

buildDynamicPrompt(options)
  ├─ Skills列表
  ├─ Session guidance
  ├─ Env info (workspace/platform/shell)
  └─ 运行时上下文 (时间/平台/发送者/频道/sessionId)
```

## 三、核心问题

### 问题1：MEMORY.md双重注入（已知，9.6KB浪费）

**两条注入路径：**
1. `staticFiles: ["MEMORY.md"]` → 读 `workspace/MEMORY.md`（§分隔的浓缩知识，8.3KB）
2. `memdir.buildMemoryPrompt()` → 读 `topics/MEMORY.md`（记忆文件索引，9.6KB）

这是**两个不同的文件**，但都叫MEMORY.md，容易混淆：
- `workspace/MEMORY.md` = 手工维护的§分隔知识（翀哥画像、经验教训、规则等）
- `topics/MEMORY.md` = auto memory框架的索引文件（CC风格，58条记忆指针）

**影响**：两个文件内容有部分重叠（如翀哥画像信息），合计17.9KB占system prompt的29%。

### 问题2：AGENTS.md过大（12.6KB，占20%）

AGENTS.md包含：
- 铁律（收到消息先记SESSION-STATE）— **核心，必须每次注入**
- 记忆恢复体系（六问恢复流程）— **核心**
- 防循环规则 — **核心**
- 通信规则 — 中等频率
- 目录表（路径映射） — **低频引用，可按需加载**
- Discord ID表 — **低频引用，可按需加载**
- 互动原则 — 中等
- 自主执行原则 — 中等

**估算**：目录表+ID表约2KB，纯参考信息，不是每轮对话都需要。

### 问题3：auto memory框架指令冗余（~7KB）

`memdir.ts`的`buildMemoryLines()`输出了完整的type定义（user/feedback/project/reference）+ when_to_save + how_to_save + what_not_to_save。这是CC verbatim移植，对Engine场景偏重——Engine的extract是自动的，agent侧主要需要"什么时候搜记忆"而不是"怎么写记忆文件"。

### 问题4：§分隔知识vs topics索引的关系不清

- `workspace/MEMORY.md`的§知识本质是"压缩版长期记忆"——把多次对话的关键发现浓缩成一段段§分隔文本
- `topics/MEMORY.md`的索引是"记忆文件目录"——指向具体文件
- 两者补充关系合理，但都在system prompt里全量注入，成本高

## 四、优化建议

### 建议0：[已完成 ✅] buildStablePrompt → buildStandardPrompt + 可定制框架

**6/14已全部实施**：
1. **BLOCK_REGISTRY**：11个block注册为积木（intro/system/doing-tasks/actions/using-tools/tone-style/output-efficiency/soul/static-files/memory-instructions/boundary）
2. **`buildStandardPrompt()`** — 标准版，固定顺序（新人开箱即用）
3. **`buildCustomPrompt()`** — 配置驱动版，支持 `order`（自定义顺序）、`exclude`（排除block）
4. **order内支持文件名**：`"AGENTS.md"` 直接作为order项，每个文件独立放置
5. **staticFiles与order互斥**：配了order就忽略staticFiles，逻辑干净
6. **方案B文件覆盖机制**：`workspace/prompts/{block-name}.md` 存在则覆盖默认函数内容
7. **两个profile已配置**：
   - 小柯：`soul → AGENTS.md → system → doing-tasks → using-tools → output-efficiency → actions → USER.md → MEMORY.md → memory-instructions`
   - 姐姐：同上，去掉actions（纯聊天陪伴）
   - 都砍掉了intro（"不是助手是人"）和tone-style（不需要）
8. **小柯prompts精简版**：system/doing-tasks/output-efficiency/actions四个文件，从6.2KB→2.6KB（省58%）

提交记录：`c55eccd`（框架+配置）→ `ec272d4`（AGENTS.md提前+order文件名）→ `2c0fc76`（staticFiles互斥）→ `77c7e32`（文件覆盖机制）

**Why:** 翀哥原话："要向插乐高一样可以定制"。后续顺序为：soul定义你是谁 → AGENTS工作方式 → system/doing-tasks工作规则 → USER/MEMORY知识背景 → memory-instructions记忆系统。

**配置语法**：
```json
{
  "prompt": {
    "order": ["soul", "AGENTS.md", "system", "doing-tasks", "using-tools", "output-efficiency", "actions", "USER.md", "MEMORY.md", "memory-instructions"],
    "exclude": ["intro", "tone-style"]
  }
}
```
- `order`中放block名或`.md`文件名（必须是staticFiles列表中的文件）
- 不列在order里的block不出现
- `boundary`永远在最后自动追加，不能被排除

### 建议1：消除MEMORY.md双重注入（节省8KB+）

**方案A（推荐）**：把`workspace/MEMORY.md`的§知识迁移到`topics/`下独立文件，通过topics/MEMORY.md索引引用。从staticFiles中移除MEMORY.md。

- 好处：消除重复，统一记忆管理路径
- 代价：§知识需要拆分成多个topic文件（工作量中等）
- 注意：§知识有些是"跨topic的浓缩画像"，不好拆。可以保留一个`topics/user_翀哥画像综合.md`

**方案B（快速）**：从staticFiles中移除MEMORY.md，但保留workspace/MEMORY.md文件。在memdir的buildMemoryPrompt中额外读取workspace/MEMORY.md并注入。

- 好处：最小改动
- 代价：仍然两份内容注入，只是换了注入点

### 建议2：AGENTS.md拆分常驻+按需（节省2-3KB）

把目录表、ID表拆到`workspace/REFERENCE.md`，从staticFiles移除。
需要时agent用read工具查（本来就要read才知道确切路径）。

```
AGENTS.md（常驻，~10KB）: 铁律 + 恢复体系 + 通信规则 + 互动原则
REFERENCE.md（按需read）: 目录表 + ID表 + 路径映射
```

### 建议3：auto memory指令精简（节省3-4KB）

Engine的agent不需要完整的type定义+write指南（extract是自动的）。保留：
- when_to_access（什么时候搜记忆）
- 精简版type说明（4个type各一句话）
- MEMORY.md索引注入（这个保留）

移除：
- 详细的how_to_save步骤（Step 1/Step 2）
- what_not_to_save的长列表
- frontmatter格式示例

### 建议4：topics/MEMORY.md索引瘦身（节省2-3KB）

当前58条，部分条目的hook描述过长（30-50字）。规则：每条hook控制在20字以内。对过长的进行压缩。

例如：
- `— 微信读取：dm=all（翀哥要求先监控所有试试）` → `— 微信dm=all监控策略`
- `— 6/13 DeepSeek flash欠费切到MiniMax...` → `— DeepSeek/MiniMax模型切换记录`

### 总结：优化空间

| 优化项 | 节省 | 难度 | 风险 |
|--------|------|------|------|
| [P0] buildStandard+customize框架 | 可变 | 中 | 架构变动，需重构成section化 |
| 消除MEMORY双重注入 | 8KB | 中 | §知识迁移工作量 |
| AGENTS.md拆分 | 2-3KB | 低 | 目录路径需read |
| auto memory精简 | 3-4KB | 低 | 需改memdir.ts |
| 索引瘦身 | 2-3KB | 低 | 信息密度降低 |
| **合计** | **15-18KB+** | | **62KB→44-47KB** |

## 五、Token成本估算

当前62KB ≈ 15,500 tokens（中文密度高，约4字节/token）

每轮API调用的system prompt成本（以DeepSeek为例）：
- 输入：15500 tokens × 0.001元/千tokens = 0.0155元/轮
- 一天100轮 ≈ 1.55元（仅system prompt部分）

优化后47KB ≈ 11,750 tokens，节省约24%。

如果用Claude/GPT-4等高价模型，节省更显著。

## 六、实施优先级

1. **P0 — buildStandardPrompt→可定制框架**：重构prompt.ts，将各部分section化，支持配置文件中定义顺序和开关。这是基础架构变动，其他优化都可在其框架下实现
2. **P1 — auto memory指令精简**：改memdir.ts，风险最低收益明确
3. **P1 — 索引瘦身**：纯文本编辑，即时生效
4. **P2 — AGENTS.md拆分**：改staticFiles配置 + 创建REFERENCE.md
5. **P3 — MEMORY.md双重注入**：需要规划§知识迁移方案
