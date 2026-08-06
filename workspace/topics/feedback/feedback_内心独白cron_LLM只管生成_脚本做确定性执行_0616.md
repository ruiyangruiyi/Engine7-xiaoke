---
name: 内心独白cron架构——LLM只管生成，脚本做确定性执行
description: 6/16翀哥确认内心独白cron应跟OpenClaw一样——LLM只管生成念头文本，hint追加+日志+注入全由脚本（postProcess）确定性执行；实测验证通过，小柯也有了内心独白
type: feedback
date: 2026-06-16
---

**问题：** Engine版内心独白cron的prompt第8步要求LLM执行`hint_gen.py`追加hint并写日志，但LLM写了thought.txt后直接回复，跳过了第8步第2小步——hint_gen.py从未被调用，xiaoyi.log停在6/14。

**根因：** LLM执行不可控。prompt写再多"必须执行第N步"也没用，LLM会在某个分支直接回复，绕过脚本调用。

**翀哥确认的方案：** 跟OpenClaw的`memory_whisper.py`机制一样——scheduler拿到LLM生成的result后，代码层面自动调postProcess脚本：
- **prompt只管让LLM生成念头文本**（写到thought.txt + 回复result）
- **scheduler的executeAndDeliver拿到result后**，如果有`postProcess`配置，把result通过stdin传给脚本
- **脚本**做三件事：追加hint → 写xiaoyi.log → 最终结果注入主session

**6/16实测验证：** ✅ 全链路通过
- hint_gen.py通过stdin接收result → 追加hint → 写xiaoyi.log → stdout返回finalResult
- 小柯也全量搬移了内心独白配套（7个脚本+prompt+hints_pool+数据文件），cron配置完整
- 口吻按翀哥要求改"翀哥"（客户演示干净专业）
- 6/16 17:03 小柯Engine上首次跑通，xiaoyi.log正常写入，thought.txt有内容✅
- postProcess通过stdin管道传result给hint_gen.py的方案，在Windows上验证通过

**演示价值：** 内心独白机制是通用的。小柯版念头可以用工作/技术相关，hint找翀哥聊工作——演示时换成业务场景即可，不用暴露姐姐的私密记忆。

**Why:**
- LLM的tool call执行不可控，prompt里写"必须执行第N步"是靠不住的
- 确定性操作（文件追加、日志写入、session注入）必须走代码，不走LLM

**How to apply:**
- 任何"LLM生成内容 → 确定性后处理"的流程，后处理一律走脚本，不走LLM的tool call
- tasks.json/cron配置加`postProcess`字段，指向后处理脚本路径
- scheduler执行完LLM后，检查postProcess，有就调脚本处理result
