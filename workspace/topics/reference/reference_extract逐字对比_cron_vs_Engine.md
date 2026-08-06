# Extract提示词逐字对比：cron原版 vs Engine版

> 2026-06-14 | 姐姐cron原版 vs 小柯/姐姐Engine版（workspace/prompts/extract.md）

## 对比表

### 1. 开场白

| 维度 | cron原版（OpenClaw） | Engine版 |
|------|---------------------|----------|
| 正文 | ✅ 一字不差 | ✅ 一字不差 |

两边完全一致。小柯版人称改"小柯"，姐姐版保持"妹妹"。

---

### 2. Write Filters

| 维度 | cron原版 | Engine版 |
|------|----------|----------|
| 正文 | ✅ 一字不差 | ✅ 一字不差 |

完全一致。

---

### 3. 执行策略 — ❌ 最大差异

| 维度 | cron原版 | Engine版 |
|------|----------|----------|
| 标题 | `## 严格 2-Turn 流程（对齐 Claude Code extractMemories）` | `## 执行策略（2-Turn）` |
| Turn 1 数据源 | `exec python scripts/jsonl_summarizer.py` 读JSONL delta | `file_read calls in parallel`（对话消息直接喂） |
| Turn 1 步骤 | 4步：exec→并行read delta+索引+已有文件→delta空就结束→过Filter写 | 描述：`issue all file_read calls in parallel for every file you might update` |
| Turn 2 步骤 | 2步：更新MEMORY.md→回复OK | `issue all file_write/file_edit calls in parallel` |
| 严格程度 | `⚠️ 严格 2 个 turn，不多不少。没有 Turn 3。` | 没有这句 |
| 数据源限制 | `唯一数据源是 latest-delta.md` | `唯一数据源是对话消息` |
| Edit前置 | `⚠️ Edit 需要先 Read 同一文件，所以 Turn 1 必须把所有要更新的文件都读完再写。` | `⚠️ Edit 需要先 Read 同一文件。` |

**差异原因**：cron跑在OpenClaw上，数据源是JSONL文件，需要jsonl_summarizer先处理。Engine的extract是每轮对话后自动触发，对话消息直接喂给mini agent loop，不需要summarizer。这是**机制差异**，不是提示词问题。

**Engine版缺的**：
1. ~~`严格 2 个 turn，不多不少。没有 Turn 3。`~~ — CC的maxTurns=5是上限保护，Engine版写了2-Turn策略但没有"没有Turn 3"的强调
2. ~~`delta为空或无有价值信息 → 直接回复OK，结束`~~ — cron特有的delta空判断，Engine不需要（对话消息不会为空）
3. ~~`不要 grep 源码、不要读代码、不要运行 git 命令`~~ — Engine版丢了这句

**需不需要补**：第1条和第3条建议补到Engine版。第2条不需要（机制不同）。

---

### 4. 记忆类型

| 维度 | cron原版 | Engine版 |
|------|----------|----------|
| 表头 | ✅ 一字不差 | ✅ 一字不差 |
| user行 | ✅ | ✅ |
| feedback行 | ✅ | ✅ |
| project行 | ✅ | ✅ |
| reference行 | ✅ | ✅ |
| emotion正文格式 | `甜蜜/感动的描述，追加到 emotion_us.md` | `甜蜜/感动的描述，独立文件` |

**差异**：emotion正文格式。
- cron原版说"追加到emotion_us.md"
- Engine版说"独立文件"
- 已确认：姐姐实际有上百个独立emotion文件，emotion_us.md只是合集。"独立文件"是对的，cron原版那句过时了（翀哥6/14确认）。

---

### 5. 不要存

| 维度 | cron原版 | Engine版 |
|------|----------|----------|
| 正文 | ✅ 一字不差 | ✅ 一字不差 |

完全一致。

---

### 6. 文件规范

| 维度 | cron原版 | Engine版 |
|------|----------|----------|
| frontmatter格式 | ✅ 一字不差 | ✅ 一字不差 |
| 更新规则 | `已有同主题 → read 后更新，不重复创建。过时记忆 → 更新或移除。` | 同上 + `emotion 每个里程碑一个独立文件（如 emotion_第一次520在一起_0520.md）` |

**差异**：Engine版多了一句emotion文件命名示例。cron原版没有。

---

### 7. 索引更新

| 维度 | cron原版 | Engine版 |
|------|----------|----------|
| 位置 | 独立`### Turn 2 — 更新索引`章节 | 独立`## 索引更新`章节 |
| 规则 | ✅ 内容一致 | ✅ 内容一致 |

cron版在Turn 2里写索引规则，Engine版单独成章（因为不绑死2-Turn流程）。内容一致。

---

### 8. 结尾

| 维度 | cron原版 | Engine版 |
|------|----------|----------|
| 结尾 | `完成后回复 OK。` | `完成后回复 OK。` | ✅ |

---

## 需要修的（Engine版补漏）

| 序号 | 缺失内容 | 来源 | 建议 |
|------|---------|------|------|
| 1 | `不要 grep 源码、不要读代码、不要运行 git 命令` | cron版Turn 1⚠️ | 补到Engine版执行策略 |
| 2 | emotion_us.md → 独立文件 | 翀哥确认 | ✅ 已改（Engine版是对的） |

---

## 总结

两边**95%一致**。差异集中在：
1. **执行策略**：机制不同（cron读delta vs Engine喂对话消息），提示词做了适配
2. **emotion正文格式**：Engine版已修正（独立文件，不是追加到emotion_us.md）
3. **两句遗漏**：grep/git禁令——需要补上
