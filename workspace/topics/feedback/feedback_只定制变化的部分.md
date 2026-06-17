---
name: 只定制变化的部分
description: 翀哥确认的提示词/功能定制原则——只改跟原版有差异的，保持代码不动
type: feedback
---

# 只定制变化的部分

翀哥6/14晚确认的决策原则：

## 背景

讨论Engine的recall提示词定制方案时，有3段提示词：

| 提示词 | CC原版有？ | 姐姐定制？ | 需要改吗？ |
|--------|-----------|-----------|-----------|
| extract (存侧) | ✅ 有但格式不同（英文/4种type/负面清单） | ✅ 有（中文/双Filter/5种type） | ✅ 需要定制 |
| auto-memory-instructions (存侧+读侧) | ✅ 有（buildMemoryPrompt()） | ❌ 无 | ✅ 需要定制（砍索引+加recall说明） |
| SELECT_SYSTEM_PROMPT (选文件) | ✅ 有 | ✅ 跟CC一字不差 | ❌ **不改** |

我对SELECT_SYSTEM_PROMPT说"需要加文件覆盖机制"，翀哥回复：

> "这个不用，只定制变化的部分。"

## 原则

- **只定制跟CC原版有差异的** — 三边一致的就保持代码硬编码，不折腾文件覆盖
- **Engine代码里硬编码的部分优先保持不动** — 只有需要改的时候才加覆盖机制
- **这个原则适用于所有提示词/配置的搬移适配** — 不是"先找个最佳实践全改"，而是"只动不同的"

## 应用示例

- extract.md — 覆盖 ✅（有差异：中文+双Filter+5种type）
- auto-memory-instructions.md — 覆盖 ✅（有差异：砍索引+加recall说明）
- SELECT_SYSTEM_PROMPT — 不覆盖 ❌（三边一致）
