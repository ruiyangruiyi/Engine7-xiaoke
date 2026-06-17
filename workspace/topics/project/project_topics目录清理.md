---
name: topics目录清理（已完成）
description: topics/根目录与子目录重复文件问题，已全部清理，根目录只剩MEMORY.md
type: project
---

# topics/ 目录清理（已完成 ✅）

## 发现（6/14晚21:00）

翀哥查看context里的 Recalled Memories 时，发现 `project_姐姐搬新家.md` 出现了两次。
根因：recall扫描 topics/ 目录时同时捡到了根目录和子目录的同一份文件。

## 清理完成（6/14晚21:13，commit `29b0ca4`）

**删除了5个重复文件**（保留较新较大的子目录版）：
- `topics/project_system_prompt优化方案.md` → 保留 `topics/project/` 版
- `topics/project_PostCompact_hook方案.md` → 保留 `topics/project/` 版
- `topics/project_姐姐搬新家.md` → 保留 `topics/project/` 版
- `topics/project_明日待办0609.md` → 保留 `topics/project/` 版
- `topics/project_CC-Agent-Teams.md` → 保留根目录版更完整

**30个根目录独有文件移入子目录**（之前散落在根目录的早期文件）：
- project_* → topics/project/
- user_* → topics/user/
- reference_* → topics/reference/
- feedback_* → topics/feedback/
- emotion_* → topics/emotion/

**最终效果：** topics/ 根目录只剩 MEMORY.md。

## 防复发

extract.md 的文件规范从 `topics/{name}.md` 改为 `topics/{type}/type_{name}.md`：
- 小柯版 + 姐姐版两版都改了
- 以后extract子agent新建文件直接写到子目录，不会再散落根目录

## 影响

- recall不再扫到同一文件两次 ✅
- context节省约2KB token（重复文件占用的空间） ✅
- 以后extract写文件自动进子目录 ✅
