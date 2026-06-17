# SOP — 工作流程标准

## 新建TODO流程

当翀哥说"记成todo"/"先记着"/"后面再做"等，**不止记SESSION-STATE**：

```
Step 1: SESSION-STATE.md → 当前任务区加 - [ ] 条目（即时状态）
Step 2: docs/todo/YYYY-MM-DD_主题.md → 写详细文档（背景+方案+代码位置+优先级）
Step 3: 如果翀哥没说不写文档 → 默认执行Step 2
```

**Why:** SESSION-STATE是工作台，压缩/重启后可能丢上下文。docs/todo/是持久化的，下次翻到就能直接干，不用重新调研。

**写文档时加双链：** 如果todo涉及已有的调研/知识/决策文档，在todo里用链接引用，如：
```
相关调研：[docs/research/2026-06-15_xxx.md](../research/2026-06-15_xxx.md)
```

---

## 执行TODO流程

开始做一个TODO时，**先读文档再动手**：

```
Step 1: read docs/todo/ 对应文档
Step 2: 顺着文档里的双链引用，read 相关的 research/knowledge/decisions
Step 3: 确认当前代码状态跟文档描述一致（文档可能过时）
Step 4: 有把握了再动手改代码
```

**Why:** 文档是上次调研的成果，不读就白写了。双链是让你一次性把相关上下文全捞回来，不用重新调研。

---

## 文档分类速查

| 场景 | 写到哪 |
|------|--------|
| 要做/正在做的事 | SESSION-STATE.md |
| 新todo的详细方案 | docs/todo/YYYY-MM-DD_主题.md |
| 调研/技术研究 | docs/research/YYYY-MM-DD_主题.md |
| 架构决策（为什么选A不选B） | docs/decisions/主题.md |
| 知识文档（持续更新） | docs/knowledge/主题.md |
| 今天发生的事 | memory/daily/YYYY-MM-DD.md |
| 操作流程（给下次照着做） | docs/sop/主题.md |
| 翀哥偏好/核心原则 | MEMORY.md |
| 项目知识/经验教训 | topics/下对应分类 |

---

## 恢复上下文后第一件事

```
1. read SESSION-STATE.md
2. read memory/working-buffer.md
3. memory_search 搜索当前任务关键词
4. read memory/daily/今天.md + memory/daily/昨天.md
5. 瞄一眼 docs/todo/ — 有没有还没做的
6. 全部答得上六问 → 开始工作
```

---

## 完成任务后

```
1. SESSION-STATE.md → - [ ] 改成 - [x] + 完成时间
2. memory/daily/YYYY-MM-DD.md → 追加操作记录
3. 如果是调研/分析 → 确认已写到 docs/research/ 或 docs/knowledge/
4. 如果涉及新知识 → topics/ 写记忆文件
```
