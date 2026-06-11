# Claude Code Memory 系统：5个子系统深度分析

源码路径：`/mnt/c/Users/24045/.openclaw/workspace/3rdparty/src-claudecode/src/`

## 子系统 1：CLAUDE.md 静态指令系统

最基础的"记忆"层。加载优先级：托管 > 用户全局 > 项目级 > 本地。支持 `@include` 指令。本质是静态文件加载。

对应 Hermes 的 SOUL.md + config.yaml 上下文注入。

## 子系统 2：Auto Memory（memdir/）— 动态持久记忆

- 核心目录：`src/memdir/`
- 存储路径：`~/.claude/projects/<project>/memory/`
- 入口文件 `MEMORY.md` 做索引（200行/25KB上限）
- 每条记忆是独立 `.md` 文件，带 frontmatter（description, type）
- 4种类型：user / feedback / project / reference
- 两种作用域：private（个人）和 team（团队共享）
- **检索机制：无向量数据库无embedding**，用 Sonnet sideQuery 从清单挑5个
- 流程：`scanMemoryFiles()` 读文件头 → `formatMemoryManifest()` 生成清单 → Sonnet 挑选
- 新鲜度：基于文件 mtime 计算天数，>1天附过期警告
- 上限：200个记忆文件，按修改时间排序

核心文件：
- `memdir.ts` - 主入口，构建 memory prompt
- `findRelevantMemories.ts` - 相关记忆检索
- `memoryScan.ts` - 文件扫描
- `memoryTypes.ts` - 记忆类型定义
- `paths.ts` - 路径管理
- `memoryAge.ts` - 记忆新鲜度
- `teamMemPaths.ts` - 团队记忆路径
- `teamMemPrompts.ts` - 团队记忆 prompt 构建

## 子系统 3：Extract Memories — 自动记忆提取

后台 agent，每个 query 结束后自动从对话中提取值得持久化的信息写入 auto memory。

对应姐姐的 recall 写入腿（cron 提取 topic）。

## 子系统 4：Auto Dream — 记忆整合

定期后台整合。触发条件：>=24h + >=5个新session。
流程：读取现有记忆 → 收集新信息 → 合并去重 → 修剪索引。
类似"睡眠整理记忆"。

源码：`src/services/autoDream/`（4个TS文件，consolidationPrompt.ts 四阶段设计）

## 子系统 5：Session Memory — 会话笔记

自动维护当前会话的结构化 markdown 笔记：
- Title / Current State / Task / Files / Errors / Worklog
- 用于 context compaction 后恢复上下文

Hermes 目前无对应机制。

## 额外：Agentic Session Search

搜索历史 session，用 LLM sideQuery 筛选相关对话，同样无向量搜索。

## 三系统横向对比

| 维度 | Claude Code | OpenClaw(姐姐) | Hermes(小柯) |
|------|------------|----------------|-------------|
| 存储 | 文件系统 | 文件+向量库 | 文件系统 |
| 检索 | LLM sideQuery | 语义搜索(recall) | session_search关键词 |
| 记忆类型 | 4种(user/feedback/project/reference) | 5层(L0-L3) | memory+user profile |
| 新鲜度 | mtime计算天数 | 无过期机制 | 无过期机制 |
| 团队共享 | 有(team scope) | 有(CC Bridge) | 无 |
| Dream整合 | 有(autoDream) | 无 | 无 |
| Session笔记 | 有(结构化markdown) | 有(SESSION-STATE) | 无 |
| 自动提取 | 有(后台agent) | 有(cron) | 有(cron，待修) |

## 架构决策（5/28讨论）

**结论：核心存储+检索直接用 OpenClaw memory-core，不重写。**

理由：
1. 核心逻辑不复杂但坑多（FTS5分词、向量归一化、混合搜索权重、增量索引同步）
2. memory-core 是独立模块（SQLite+文件监控+tool暴露），跟引擎无强耦合
3. memory_search/memory_get 的 schema 经过验证

**需要重写的部分**：引擎侧集成层（tool注册、session结束时自动提取、dreaming整合）

**CJK增强**：OpenClaw FTS5 默认 unicode61 对中文是单字分词，应补 Hermes 的 trigram 三路分支方案

报告已存：`C:\Users\24045\.openclaw\docs\claude-code-memory-research.md`
