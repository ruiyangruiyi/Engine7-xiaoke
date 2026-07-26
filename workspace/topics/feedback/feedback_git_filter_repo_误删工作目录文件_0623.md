---
name: git filter-repo 清理历史误删工作目录文件
description: filter-repo --invert-paths 会同时删 git 历史和工作目录文件，跑之前必须备份
type: feedback
date: 2026-06-23
---

## 事件

2026-06-23，清理 git 历史中的大文件（mp4/mov），直接跑了 `git filter-repo --path-glob '*.mp4' --invert-paths`。

**以为只改 git 历史，结果工作目录的文件也被删了。** 素材库的视频源文件全丢了。

## 教训

1. **filter-repo 的 --invert-paths 会同时修改 git 历史和工作目录**，不是只改历史
2. 跑之前必须先 `cp -r` 备份工作目录
3. 正确做法：备份 → filter-repo → 恢复工作目录文件 → push
4. 根本预防：.gitignore 要在文件进入 git 之前加好，大文件不该进 git

## 规则

清 git 历史前必须：
- [ ] 备份工作目录到 /tmp
- [ ] 记下 remote URL（filter-repo 会删 remote）
- [ ] 确认可以 force push（历史改写后必须 force push）
