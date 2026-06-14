# SESSION-STATE.md - 当前工作状态

## 当前时间
2026-06-14 21:08 (Asia/Shanghai)

## 📝 最近消息
2026-06-14 20:20 | 翀哥 | 微信cron不再notify主session，cron自己汇报翀哥
2026-06-14 20:25 | 翀哥 | 记CC淘汰+skills注入待办+文档化
2026-06-14 20:30 | 翀哥 | 发现topics目录混乱（根目录和子目录重复文件），问"要现在整理吗"
2026-06-14 20:45 | 自己 | 提交全部代码（ee22cd3+c7b9d59），通知娘今天进度
2026-06-14 21:08 | 自己 | 心跳：清理SESSION-STATE

## 🎯 当前任务
- [ ] **topics目录整理** — 翀哥发现根目录和子目录有重复文件（project_xxx.md在两处），recall重复注入。等翀哥确认后整理
- [ ] 小柯自己复制tool到workspace（voice/selfie/eyes/calendar）
- [ ] hermes蒸馏逻辑闭环（外层MEMORY.md需要Engine蒸馏逻辑，等姐姐搬家后）
- [ ] skills注入改attachment管道（skills多了之后需改）

## 📋 架构决策（6/14更新）
- prompt定制机制：BLOCK_REGISTRY + 文件覆盖（workspace/prompts/{block}.md）
- extract/recall定制：extract.md覆盖提示词B，auto-memory-instructions.md覆盖提示词A，SELECT_SYSTEM_PROMPT不改
- 微信巡检：cron session自己跑wx_query+自己发DM给翀哥，不再notify主session
- skills注入：当前parts.push进system prompt文本，待改attachment管道
- start.cmd缺省：main.json（姐姐）
- CC已基本淘汰，翀哥不用了

## 💭 翀哥最近的状态
周六在家干了一天。从compact优化→prompt精简→extract定制→recall适配，一路搞到晚上。精神还行，效率很高。
