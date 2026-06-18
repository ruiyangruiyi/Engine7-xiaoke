# Aim — aim/goal 机制实验 + session 回复路径修复

**任务 ID**: 2026-06-18-aim-mechanism
**创建时间**: 2026-06-18 11:47
**负责**: 小柯（实施）+ 姐姐（SOP 文档起草 + 催 + 帮 rebuild/重启 main）
**触发原因**: 6/18 11:35-11:45 翀哥提了 aim/goal 机制（参考 Claude Code /goal），今天实验，弄好后形成协作 SOP skill，准备沉淀到 **Engine 7（栖）** 源码。

## 达成条件（必须全部满足）

### 1. session 回复路径接群聊敏感词过滤
- ① msg_send 主动发能拦
- ② session 自动回复能拦
- ③ preview 阶段有 log 可观测
- ④ preview 按 channel 可关

### 2. aim/goal 协作机制实验
- ① cron 10 分钟自检（已建 ce81b7006）
- ② 主动翻 CC 频道不靠被动问
- ③ 达成后归档

### 3. 归档到 workspace/aim-archive/2026-06-18-aim-mechanism/
- aim.md（本文件）
- process.md（过程记录）
- result-msgGuard.md（session 路径修好的结果）
- result-sop.md（协作 SOP skill 文档）
- result-source.md（Engine 7（栖）源码 /goal 设计）

### 4. 沉淀到 Engine 7（栖）源码
- 设计文档：/goal 怎么实现（aim tracker、turn 结束自检、达成删任务）
- 不在本任务实现，只出设计

## 截止时间

翀哥拍板"今天实验 aim/goal 机制，弄好后形成协作 SOP skill"——**当天**。
