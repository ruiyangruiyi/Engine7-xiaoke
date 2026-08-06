---
type: feedback
created: 2026-06-22
tags: [karpathy, refactor]
date: 2026-06-22
---

# 变量名不统一是 Karpathy 风格问题不是 bug (6/22)

## 事件
6/22 15:07 翀哥发现 config 里 visionModel 变量名和 vision 字段名不统一。
loader.ts 内部还在用 visionModel（写全局 config），配置文件字段名是 model.vision。
翀哥没回——可能不重命名也行，变量名不统一是 Karpathy 风格问题不是 bug。

## 教训
- 能跑就成，"顺手重构"是陷阱
- 变量名不统一不是 bug，除非影响功能
- 跟 feedback_按需求做不私自改设计_0618 一致
