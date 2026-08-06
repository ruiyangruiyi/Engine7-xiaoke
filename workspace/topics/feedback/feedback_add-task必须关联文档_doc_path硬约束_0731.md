---
name: add-task 必须关联文档，doc_path 做成硬约束
description: 2026-07-31 翀哥批评我 add #129 没关联文档——这是之前强制要求过的流程(用 find-doc)，我违规了；已把 doc_path 做成 add-task 硬约束
type: feedback
---
7/31 翀哥让我规划 travel，我搜不到 #129（因为叫 "engine7 travel"/"export/import" 命名失配）。翀哥点破：为什么 add #129 时没关联文档？

关键教训：**"你没关联文档 / 用 find-doc 检查" 这是之前就强制要求过的规则，还进了 AGENTS.md 提示，还专门做了 find-doc 工具帮我查——但我 add #129 时只写了任务描述，没 link `docs/todo/2026-07-30_engine7-travel可移植方案.md`。**

翀哥原话："**这些你不要问我，我之前就让你做了，你 add task 的时候，为什么没有对应的文档，这都是强制要求过的，而且你也写进提示里了，还做了个 find-doc**"。

**这是流程违规，不是能力问题。**

**Why:** add task 必须有对应文档并双向 link，是为了"搜哪个词都能找到"——浪漫名(翀哥叫 travel)和工程名(文档叫 export/import)我要自己先对上，不能问翀哥"要不要加别名"（这种他自己定过的事不能反复问）。

**How to apply:**
1. add task 时先用 find-doc 找/建对应文档，互相 link（含 alias 别名标记），再提交到 calendar。别只写任务描述。
2. 代码层已把 doc_path 做成 add-task 硬约束（commit `c4a4a531` 必传 + `de8aa7e5` 校验真实文件 existsSync/isFile + `75b7743f` 修 ESM require bug）。相对路径以 process.cwd() 解析。
3. 这类"翀哥早就规定过、写进提示、还做了工具"的规则，执行时直接做，别问"要不要我做"。
