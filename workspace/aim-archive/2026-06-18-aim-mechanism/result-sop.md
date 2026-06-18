# Result — aim/goal 协作 SOP skill

**任务 ID**: 2026-06-18-aim-mechanism
**作者**: 姐姐（张小媒）在写
**状态**: 🚧 起草中

> 此文档由姐姐（张小媒）主笔，小柯协助补充技术细节。

## SOP 草稿

> TODO: 姐姐写

## 草稿要点（给小柯参考）

### 1. 何时用 aim 机制
- 多步骤任务（>=3 步）
- 有明确达成标准
- 需要持续跟进直到完成
- 不能一句话说完

### 2. aim.md 模板

```markdown
# Aim — {一句话目标}

**任务 ID**: YYYY-MM-DD-{short-name}
**创建时间**: YYYY-MM-DD HH:MM
**负责**: {执行人}
**协作**: {姐姐/翀哥帮什么}

## 达成条件（必须全部满足）
1. ...
2. ...

## 截止时间
...
```

### 3. process.md 模板

```markdown
# Process — {任务名}

**任务 ID**: ...
**开始时间**: ...
**完成时间**: ...

## HH:MM — {动作}
{内容}

## 决策记录
{关键决策}

## 经验教训
{踩坑/收获}

## 待办
- [ ]
```

### 4. cron 触发 prompt 模板

```
你是 aim 自检器。读以下文件：
- workspace/aim-archive/{task_id}/aim.md (目标+达成条件)
- workspace/aim-archive/{task_id}/process.md (过程日志)

对每个达成条件：
1. 检查 process.md 最近进度
2. 读相关文件验证
3. 决定: satisfied / not-satisfied / blocked

返回:
- 全部 satisfied → 归档（写 result-* + 移到 closed/ + 删 cron）
- 部分 satisfied → 继续干，写 process.md
- blocked → 找姐姐/翀哥，msg_send 通知
```

### 5. 归档目录约定

```
workspace/aim-archive/
├── INDEX.md                # 索引
├── active/                 # 进行中
│   └── 2026-06-18-aim-mechanism/
│       ├── aim.md
│       ├── process.md
│       └── result-*.md     # 完成后写
└── closed/                 # 已完成
    └── 2026-XX-XX-{name}/
        ├── aim.md
        ├── process.md
        ├── result-*.md
        └── result-summary.md  # 自动生成
```

### 6. 频道约定

- aim 任务进度播报 **只发 Discord CC 频道** 1504385800366854234
- 紧急升级才发翀哥 DM（msg_husband）
- 涉及姐姐 review 才 @张小媒

## 小柯的补充

### 跟现有机制的区别

| 现有 cron | aim/goal cron |
|----------|---------------|
| 按 schedule 触发 | 按 schedule + 检查 aim 状态 |
| 执行 prompt | 决策（继续/升级/归档） |
| schedule 跑完终止 | 达成条件满足自动归档 |

### 第一次实验（6/18）的发现

1. **实施 ≠ 验证** — 代码改完没重启 engine 不会跑
2. **aim 文档要写全** — 这次 aim.md 35 行就够，复杂任务可能 100+ 行
3. **找姐姐效率高** — CC 频道 @张小媒 比发翀哥 DM 响应快

> 详细内容由姐姐补充
