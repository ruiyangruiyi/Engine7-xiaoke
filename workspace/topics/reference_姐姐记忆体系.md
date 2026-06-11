---
name: 姐姐的记忆体系
description: 张小媒五层记忆架构（L0-L3）详情，topic-recall机制，filter逻辑，姐妹记忆体系对比
type: reference
keywords: [姐姐, 记忆, 五层, topic-recall, manifest, OpenClaw, 索引, filter, 提取]
created: 2026-04-20
updated: 2026-06-08
---

## 姐姐五层记忆架构

- **L0 身份层**：SOUL.md + IDENTITY.md（不变的人格）
- **L0.5 主题召回**：topics/*.md + topic-recall插件（before_prompt_build钩子）
- **L1 索引层**：memory/INDEX.md（254行，所有知识文件的总目录+链接地图）
- **L2 知识层**：docs/*.md + memory/*.md（~20个文件，541KB，双向链接）
- **L3 日志层**：memory/YYYY-MM-DD.md（9.1MB，38天）

## topic-recall插件流程

1. 用户发消息 → before_prompt_build钩子触发
2. 扫描topics/*.md的frontmatter → 建manifest
3. 用轻量模型(glm-4.7)选最相关的3个文件
4. 读取内容 → 截断保护 → 注入到system-reminder
5. agent回复时脑子里已经有了相关记忆

## 两条腿

- **写入腿**：cron定时扫描对话 → 提取关键信息 → 生成topic文件 + 更新INDEX
- **读取腿**：recall根据用户消息 → 从manifest选文件 → 注入上下文

**6/8翀哥确认**：在Engine新家里，两条腿的分离更彻底——topics只走recall不进向量索引，向量索引（OpenClaw memory-core）只负责session对话内容。两个系统并行运作，互不干扰。

## 写入腿的Filter逻辑（5/14确认）

**按类型各走各的filter，不是AND关系：**

| 类型 | 何时保存 | Filter |
|------|---------|--------|
| user | 翀哥的角色/偏好/知识背景 | Surprising |
| feedback | 翀哥纠正或确认做法时 | Surprising |
| project | 项目进展/决策/截止日期 | Surprising |
| reference | 外部系统资源指针 | Surprising |
| emotion | 第一次 or 关系转折点 | Milestone |

- **Surprising Filter**：未来会用到？且无法从代码/git/已有记忆推断？两个YES才写
- **Milestone Filter**：只记"第一次"和"转折点"，不记重复模式
- 实际/情感类走Milestone，事实类走Surprising

### 小柯之前的错误理解

把两个filter当成了"所有内容都要过两个"的AND关系，导致Write Filter过严、大量内容被过滤掉。
翀哥指示：直接抄姐姐的提示词，不用自己理解再写一遍。

### 采集方式差异

- **姐姐**：jsonl_summarizer.py直接读session JSONL文件 → 读摘要 → 判断 → 写入
- **小柯（bug版）**：session_search搜对话 → 看原文 → 判断 → 写入
  - Bug：session_search搜不到活跃session，导致正在进行的对话被漏掉
  - 修复方向：改成像姐姐那样直接读JSONL

## 姐姐记忆规模

- memory/ 9.1MB（38天）
- topics/ 276KB（~30个L0.5文件）
- docs/ 541KB（~20个L2文件）
- INDEX.md 254行
