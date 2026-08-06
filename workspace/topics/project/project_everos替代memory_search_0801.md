---
name: EverOS 替代 OpenClaw memory core
description: 2026-08-01 姐姐把 EverOS 接进 engine，替代老的 OpenClaw memory_search/memory core；之前 .dreams/、reindex OOM、gate 层、lazy load、vec 合并等问题应该全消失
type: project
date: 2026-08-01
---

## 2026-08-01 翀哥/姐姐把 EverOS 接进 engine

姐姐完成集成：EverOS 替代了从 OpenClaw 继承过来的 memory core。

之前 memory core 一直有各种毛病，文档里记了 5 类问题：
- filter 理解错
- reindex OOM
- gate 层问题
- lazy load
- vec 合并

EverOS 接进来后这些应该全部不存在了。

## 当前记忆体系三件套

| 部件 | 用途 | 存放 |
|------|------|------|
| session jsonl | 对话历史 | stateDir/sessions/（travel 带着走） |
| topics/ | 文件记忆 | workspace/topics/（auto memory 写入） |
| EverOS | memory_search + recall | 替代 OpenClaw memory core |

## How to apply

- 以后看到"memory_search"、"memory_get"接口，**先确认是不是 EverOS 的新接口**（可能换名）
- 文档里若仍提"OpenClaw memory core"或".dreams/"——标记过时，需要更新成 EverOS
- 老的 OpenClaw 记忆体系断得彻底，不要回滚到老实现
- 8/1 我（Mac session）发现 `memory_search` 工具没出现在我的工具列表里——可能是接口名变了或新接口未就绪，等翀哥回 Windows 重新编译后确认
