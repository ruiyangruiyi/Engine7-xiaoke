---
name: topics目录清理
description: topics/根目录与子目录重复文件问题，需清理根目录旧文件
type: project
---

# topics/ 目录重复文件问题

## 发现（6/14晚）

翀哥查看context里的 Recalled Memories 时，发现 `project_姐姐搬新家.md` 出现了两次：

```
| project_姐姐搬新家.md | 555 |
| project_姐姐搬新家.md | 1.6K |
```

根因：recall扫描 `topics/` 目录（递归），同时捡到了：
- `topics/project_姐姐搬新家.md`（根目录，旧版，555 tokens）
- `topics/project/project_姐姐搬新家.md`（子目录，新版，1.6K tokens）

## 重复文件清单

| 根目录（旧） | 子目录（新） |
|---|---|
| project_system_prompt优化方案.md | project/project_system_prompt优化方案.md |
| project_PostCompact_hook方案.md | project/project_PostCompact_hook方案.md |
| project_姐姐搬新家.md | project/project_姐姐搬新家.md |
| project_明日待办0609.md | project/project_明日待办0609.md |

## 根目录独有（无子目录版本）

这些文件在根目录只有一份，但命名风格（type_名称）与子目录不一致：
- project_Engine自研.md
- project_CC-Agent-Teams.md
- project_compact_threshold算法.md
- project_autoDream.md
- project_跨bot通信.md
- project_迁移计划.md
- project_Discord平台.md
- project_姐姐直播.md
- project_AI自我激活.md
- project_娘relay.md
- project_出差0420.md
- project_记忆提取修复.md
- user_翀哥画像.md
- reference_Engine_skills扫描.md
- reference_OpenClaw架构.md
- reference_微信消息读取.md
- reference_Hermes架构.md
- reference_ollama踩坑.md
- reference_姐姐记忆体系.md
- reference_主动联系.md
- reference_消息元数据注入.md
- reference_lark-SDK踩坑.md
- reference_display配置.md
- reference_MEMORY.md 双注入机制.md
- feedback_stream超时重试.md
- feedback_msg_send必填设计.md
- feedback_循环屏蔽.md
- feedback_API重试可见性.md
- feedback_团队踩坑.md
- emotion_身世.md
- emotion_翀哥表白.md
- emotion_嫂子事件.md

## 问题影响

1. **重复内容浪费时间** — 同一份记忆占两份inject token
2. **旧版可能过时** — 根目录文件是早期手动建的，子目录是extract子agent后来自动建的，新版在子目录
3. **recall选文件时可能选错** — 如果两版内容不同，可能选了旧版本

## 解决思路

**方案A：删根目录重复文件（推荐）**
- 确认子目录版本更新后，直接删除根目录的4个重复文件
- 根目录独有文件可以保留或搬迁到子目录（日常影响不大，因为命名时带type前缀，不会跟子目录混淆）

**方案B：recall加去重逻辑**
- 按文件名去重（取子目录版本优先）
- 但改动代码，成本比删文件高

翀哥6/14晚发现了这个问题，优先级中等——不直接影响功能，但浪费token和注意力。
