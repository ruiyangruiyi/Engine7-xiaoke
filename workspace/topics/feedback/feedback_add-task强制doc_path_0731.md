---
name: add-task 必须强制关联真实文档（doc_path 硬约束）
description: 2026-07-31 #129 没关联 docs 被翀哥批评，把 add-task 改成必传+存在校验的硬约束
type: feedback
---
# add-task 强制 doc_path 硬约束

## 事实
7/31 travel 排查发现 #129 任务没关联 `docs/todo/2026-07-30_engine7-travel可移植方案.md`。翀哥严厉纠正："这些你不要问我，我之前就让你做了，你 add task 的时候，为什么没有对应的文档，这都是强制要求过的，而且你也写进提示里了，还做了个 find-doc。"

**这是流程违规，不是能力问题**——add-task 有强制文档要求，但我 add #129 时只写任务描述没关联文档。

## 修复（三层校验）
1. **必传**（`c4a4a531`）— add-task 不传 doc_path 直接报错，提示去哪建、怎么命名
2. **文件存在**（`de8aa7e5`）— `fs.existsSync(docPath)` 真存在
3. **是文件不是目录**（`de8aa7e5`）— `statSync().isFile()`

相对路径以 `process.cwd()` 解析（engine 启动已 chdir 到 workspace，`docs/todo/xxx.md` 能正确找到）。

## Why
翀哥明确强制要求：**执行 add task 时必须有对应文档并互相链接**，用 find-doc 查找。**不得再询问是否该做**——这是底线规则不是可选项。

## How to apply
- add task 前先 find-doc 找对应文档，找到后关联 doc_path + url
- 无文档就先建 `docs/todo/YYYY-MM-DD_标题.md` 再 add task
- 别再问翀哥"要不要加别名/要不要加文档"，直接做
