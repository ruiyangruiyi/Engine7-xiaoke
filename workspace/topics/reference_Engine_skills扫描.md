---
name: Engine Skills扫描器限制
description: Engine的scanner.ts只认SKILL.md不认DESCRIPTION.md，导致大部分skills不可用；从TestEngine搬了docx/pdf/pptx/xlsx
type: reference
---

## 问题

小柯在Engine下查可用skills，只有2个：`dogfood`和`yuanbao`。明明带了20多个skills过来，大部分不可用。

## 根因

Engine的`scanner.ts`只识别`SKILL.md`文件名，但大部分skill目录（继承自Claude Code/Hermes）用的是`DESCRIPTION.md`。只有`dogfood/SKILL.md`和`yuanbao/SKILL.md`两个符合条件，其余全部被跳过了。

## 临时解决（6/8）

从TestEngine的skills目录搬了4个办公类skill到小柯的`D:\xiaoke\skills\`：
- **docx** — Word文档
- **pdf** — PDF文档
- **pptx** — PowerPoint演示文稿
- **xlsx** — Excel表格

重启后scanner可识别。

## 根本修复方向

改`scanner.ts`让它同时识别`SKILL.md`和`DESCRIPTION.md`两种文件名——这样20多个skill都能自动可用，不用逐个搬运。

**Why:** 当前scanner规则跟Claude Code标准skill目录结构不兼容，导致大部分skill不可见。搬运只是治标，改scanner是治本。

**How to apply:** 如果发现skills列表比预期少很多，先检查skill目录下是SKILL.md还是DESCRIPTION.md，再对比scanner.ts的匹配逻辑。

**注意（6/8）：** 翀哥的意思是从TestEngine搬4个skills（docx/pdf/pptx/xlsx）就够了，不需要改scanner让全部DESCRIPTION.md的都进来——太多了反而可能不适用。4个办公类已通过拷贝方式加入，重启生效。
