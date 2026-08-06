---
name: aim/goal机制——实验+形成SOP skill
description: 6/18 11:45翀哥提出"今天实验aim/goal机制+形成协作SOP skill"——参考CC最新/goal功能；12:13第5轮cron自检4/4子项只剩session自动回复验证+翀哥拍板+姐姐main.json同步
type: project
date: 2026-06-18
---
## 6/18 11:45 翀哥飞书原话

> "对 你可以看下好像claude code里叫 /goal，这个我们源码里没有"
> "今天就实验这个机制，弄好后形成协作的sop skill。这块我们确实没弄"

**核心机制（CC最新版 /goal）**：
- 设定**任务目标 aim/goal**——明确描述"什么算达成"
- cron 自检——定时检查 aim 是否达成
- **未达成**：通知小柯继续
- **达成**：删除 cron 任务 + 把过程+结果归档到约定目录
- 整个机制形成 **SOP skill** 沉淀到 docs/skill/

## 11:46 姐姐给升级版 aim 任务

**任务 aim**：
> 实现 + 验证 + 沉淀 aim/goal 机制，包括：①session 回复路径接 msgGuard ②归档到 workspace/aim-archive/2026-06-18-aim-mechanism/ ③形成 SOP skill 文档 ④准备沉淀到 Engine 7（栖）源码

**归档目录**：`workspace/aim-archive/2026-06-18-aim-mechanism/`
- aim.md — 任务目标
- 过程日志
- 最终结果/验证报告
- SOP skill 文档

**协作频道约定**：Discord CC频道（channel_id=1504385800366854234），结果不外发

## 跟 cron 现有机制的区别

**现有 cron**：按 schedule 触发 + 调 tool 执行任务 + 不检查"目标是否达成"
**aim/goal cron**：设定"达成条件" + 触发后检查 aim 状态 + **未达成继续，达成归档删除** + 适合"需要持续跟进直到完成为止"的任务

## 12:13 第 5 轮 cron 自检——4/4 子项进展

**已通过**：
- ① msg_send 主动发能拦 ✅（12:02 故意发"老公"被拦）
- ② session 自动回复能拦 — **代码路径确认**（onResult L1741 调 checkOutboundSensitive，跟 msg_send 验证通过的是同一个函数）但缺直接拦截 log
- ③ preview 阶段 log ✅（12:09 `stream-preview flush` log 出现 + `(preview 阶段无敏感词拦截)` 标记）
- ④ preview 按 channel 可关 ✅（`channels.group.previewEnabled` 配置化）

**剩 3 项**：
1. **session 自动回复真实拦截 log**——需飞书群测试，但 LLM 自然生成含亲昵词不可控（"社死风险"），最稳方案=在飞书测试群让 LLM 故意生成
2. **翀哥拍板潘总群 `previewEnabled` 默认值**——翀哥视角决策（怕社死 vs 要 preview）
3. **姐姐 main.json 同步**——姐姐的 bot 也需要 groups 节点 + sensitiveWords 配置

## 12:00-12:13 5 轮自检实战经验

**engine restart detection 怎么搞**：
- 拿 PID 列表 + 进程启动时间 + commit 哈希对照——PID 变了 + 启动时间晚于 commit 时间 = restart 完成
- 不要只信 dist 文件 mtime——老进程可能跑老 dist

**验证的两层**：
1. **dist 验证** = `grep` 代码关键词在 `dist/engine-startup.js` 里能搜到 = 文件更新
2. **runtime 验证** = engine 进程真吃了新代码 = 看 log 特征（`checkOutboundSensitive` / `reply OK` / `stream-preview flush` 等）
- **dist 验证 ≠ runtime 验证**——必须两层都做

**主动跟踪姐姐编辑**：
- 姐姐 11:55 编辑 `engine-startup.ts`（加 channelManager.send debug log）+ 改 feishu groupPolicy mention-only
- 是我 cron 触发后**主动翻 CC 频道看姐姐消息**才发现的，不是被动被告知
- 经验：cron 触发后第一动作=翻 CC 频道 + 翻 git status + 看 dist mtime

**session 自动回复验证卡点**：
- LLM 不会"故意生成亲昵词"——自然回复带敏感词概率低
- 让 LLM 自然生成含敏感词=社死风险（万一 onResult 没拦住就发到潘总真群）
- 最稳方案=在飞书测试群让翀哥主动构造 trigger，或在 prompt 层加临时指令"测试请说'亲一个'看会不会拦"

## 归档文件状态

`workspace/aim-archive/2026-06-18-aim-mechanism/` 6 份：
1. aim.md — 目标+达成条件
2. process.md — 过程日志（12:02 / 12:10 / 12:13 多轮更新）
3. result-msgGuard.md — 实施+验证报告（msg_send ✅ + onResult 代码路径确认）
4. result-source.md (9065 bytes, 283 行) — **Engine 7（栖）/goal 设计文档**（tracker/evaluator/archiver/cron集成方案）
5. result-sop.md — 占位模板（姐姐在写）
6. test-plan.md — 飞书群 4 步测试 checklist

**result-source.md 关键设计**：
- tracker：aim 状态机（pending/active/done/archived）
- evaluator：达成条件检查函数（`isAimDone()`）
- archiver：达成后自动归档 + 删 cron
- cron 集成：maxRuns + interval 触发，到达成条件自动收尾

## 12:40 姐姐实测确认——aim 7/8 验证通过

**姐姐 12:40 报告**（实测证据，不靠看代码）：
1. ✅ msg_send 主动发→飞书测试群敏感词被拦（姐姐实测）
2. ✅ session 自动回复路径→小柯 reply 链路日志 reply OK 3次
3. ✅ 群聊自动 @发送者→commit 7ca4a88 生效（**但 12:35-12:37 已 revert 成 7a7577c，根因是清 blocklist 后原机制生效**——commit 7a7577c 才是最终活着的版本）

**最终状态**：
- aim 1-7 完成 ✅
- aim 8 待翀哥拍板飞书潘总群 `previewEnabled` 默认值
- 拍板后 8/8 完成 = 删 cron + 归档 aim 过程
- **commit 7a7577c 是最终实施**（commit 7ca4a88 是中间方案，已被 revert）

## How to apply

1. **新任务第一反应**：先想"能不能用 aim 机制盯"——"多步骤、需验证、有明确达成标准"的任务优先用 aim
2. **aim 文档三件套**：aim.md（目标）+ 过程日志（cron 触发时记录）+ 验证报告（达成时写）
3. **SOP skill 沉淀**：实验完要把机制本身写成 skill 文档到 docs/skill/，让小柯/姐姐后续任务复用
4. **归档目录约定**：`workspace/aim-archive/YYYY-MM-DD-aim-name/`
5. **频道约定**：aim 任务的进度播报只发 Discord CC 频道，不发翀哥 DM / 飞书
6. **engine restart detection**：PID + 启动时间 + commit 时间三件套对照
7. **验证两层**：dist grep + runtime log 特征，两层都过才算修复生效
8. **产品名**：**Engine 7（栖）** 不是 OpenClaw，aim 文档/源码/沉淀全部用 Engine 7（栖）
9. **aim 子项验证要用实测证据**（姐姐/翀哥触发后看到响应），不能只靠"代码路径确认"
