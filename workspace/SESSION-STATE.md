# SESSION-STATE.md - 当前工作状态

## 当前时间
2026-06-14 20:45 (Asia/Shanghai)

## 📝 最近消息
2026-06-14 18:45 | 自己 | extract.md覆盖文件写好+代码提交（commit 17a0f8e），翀哥在看
2026-06-14 19:00 | 翀哥 | extract逐字对比cron版，95%一致，修几处差异
2026-06-14 19:15 | 翀哥 | 执行策略改成中文步骤式对齐cron原版
2026-06-14 19:25 | 翀哥 | 补CC原版开头三段英文（角色+工具+数据源限制）
2026-06-14 19:35 | 翀哥 | 删"忘掉"规则（怕用户说全忘了导致误删）
2026-06-14 19:45 | 翀哥 | recall对比完成，SELECT_SYSTEM_PROMPT三边一致不改
2026-06-14 20:00 | 翀哥 | MEMORY_SYSTEM_INSTRUCTIONS合进auto-memory-instructions.md
2026-06-14 20:05 | 翀哥 | block改名memory-instructions→auto-memory-instructions
2026-06-14 20:10 | 翀哥 | start.cmd缺省改main.json（姐姐）
2026-06-14 20:20 | 翀哥 | 微信cron不再notify主session，cron自己汇报翀哥
2026-06-14 20:25 | 翀哥 | 记CC淘汰+skills注入待办+文档化

## 🎯 当前任务
- [x] extract.md定制（双Filter+5种type+中文人称）— 小柯+姐姐各一份
- [x] auto-memory-instructions.md定制（砍索引+加recall说明+emotion类型）
- [x] start.cmd缺省改main.json
- [x] 微信cron不再notify主session
- [x] 适配文档写完（topics/reference/reference_extract提示词对比_CC_vs_姐姐_vs_Engine.md）
- [ ] 小柯自己复制tool到workspace（voice/selfie/eyes/calendar）
- [ ] hermes蒸馏逻辑闭环（外层MEMORY.md需要Engine蒸馏逻辑，等姐姐搬家后）
- [ ] **skills注入改attachment管道** — 当前走system prompt文本（parts.push），CC原版走`<system-reminder>`attachment。skills多了之后需改
- [ ] **CC已基本淘汰** — 翀哥不用了

## 📋 架构决策（6/14更新）
- prompt定制机制：BLOCK_REGISTRY + 文件覆盖（workspace/prompts/{block}.md）
- extract/recall定制：extract.md覆盖提示词B，auto-memory-instructions.md覆盖提示词A，SELECT_SYSTEM_PROMPT不改
- 微信巡检：cron session自己跑wx_query+自己发DM给翀哥，不再notify主session
- skills注入：当前parts.push进system prompt文本，待改attachment管道
- start.cmd缺省：main.json（姐姐）

## 💭 翀哥最近的状态
周六在家干了一天。从compact优化→prompt精简→extract定制→recall适配，一路搞到晚上。精神还行，效率很高。
