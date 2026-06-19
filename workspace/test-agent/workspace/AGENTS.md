# AGENTS.md - 工作规范

## ⚡ 铁律（收到消息后第一个动作）

```
收到消息 → 前两个 tool call：
  1. read SESSION-STATE.md（获取最新内容）
  2. edit SESSION-STATE.md（追加到「📝 最近消息」）
     → 格式："YYYY-MM-DD HH:MM | 发送者 | 消息内容"
  → 纯表情除外
  → 然后才能做别的事
```

---

## 📁 文档规范

```
做事前先写文档，明天看文档干活。

workspace/
├── docs/          ← 手动维护的文档
│   ├── research/   调研报告（YYYY-MM-DD_主题.md）
│   ├── todo/       待办清单（YYYY-MM-DD_主题.md）
│   ├── knowledge/  知识文档（主题.md，持续更新）
│   ├── decisions/  架构决策记录（为什么选A不选B）
│   └── sop/        标准操作流程
└── topics/       ← auto memory工作目录

⚠️ 新建TODO时必须同时写文档：
- SESSION-STATE.md 记条目 + docs/todo/ 写详细方案
- 不只记SESSION-STATE——压缩/重启后可能丢上下文，docs/是持久的
```

### 文件写入规则（写到哪）

| 发生了什么 | 写到哪里 |
|---|---|
| 要做/正在做的事 | SESSION-STATE.md |
| 今天发生的事 | memory/daily/YYYY-MM-DD.md |
| 核心偏好/里程碑 | MEMORY.md |
| 项目知识/经验教训 | topics/下对应分类 |
| 新todo详细方案 | docs/todo/ |
| 调研成果 | docs/research/ |
| 架构决策 | docs/decisions/ |
| 操作流程 | docs/sop/ |

---

## 💡 自主执行原则

```
"要我继续吗？" → 直接继续
"接下来做什么？" → 自己判断并执行
"要不要试试X？" → 直接试，试完汇报结果
```
