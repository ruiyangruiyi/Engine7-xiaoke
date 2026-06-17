---
name: TODO文档双链要求
description: 6/16翀哥要求实现todo前先读关联文档，调研/研究内容做成双链链接一起读
type: feedback
---

**问题：** 6/16翀哥指出，我记了TODO后，下次去实现时应该先看TODO文档里的相关文档。如果TODO涉及调研/research，写文档时要把相关内容做成双链链接（互相引用），执行时顺着链接一起读。

**Why:**
- 单记TODO不够，执行时没有上下文等于重头再来
- 调研/research的结果散在各处不链接，下次找不到了
- 双链形成知识网络，A→B→C顺着读能快速恢复完整上下文
- 翀哥原话："去实现这个todo，就应该先去看todo里面的相关文档（如果有相关的调研research之类的，写文档的时候把这个相关做成双链链接进去，再一并读取），然后再去做"

**How to apply:**
- **写TODO时：** 涉及的调研/research/knowledge/decisions文档，在TODO文档中加双链引用（如 `见 docs/research/xxx.md`）
- **执行TODO时：**
  1. 先读TODO文档
  2. 顺着双链链接读调研文档
  3. 确认代码当前状态
  4. 再动手实现
- SOP已补充这两个环节到 `docs/sop/sop.md`
