---
name: Vision路由——有图始终走vision模型，不被/model override劫持
description: 6/17发现/model切模型后图片消息也走override模型（可能不支持视觉），修复为有图始终走visionDeps
type: feedback
date: 2026-06-17
---

6/17 发现 vision 路由问题：`/model` 临时切模型后，图片消息也走 override 模型（override 的模型可能不支持视觉），导致图片消息处理失败。

**根因：**
```
之前的路由优先级：modelOverride > vision > default
→ /model 切了之后，图片也走 override 模型，不走 vision
→ 如果 override 的模型不支持视觉（如 deepseek-v4-pro），图片消息就炸了
```

**修复：**
```
新的路由优先级：vision（有图） > modelOverride > default
→ 有图片 → 始终走 visionDeps，无视 modelOverride
→ 纯文本 → 走 modelOverride（如果设置了）或 default
```

**Why:** Vision 模型（如 Minimax-M3）是专门处理图片的多模态模型。`/model` 切的是"文本模型"——用户切模型是为了更好的文本体验，不代表他想让图片也走不支持视觉的模型。视觉和文本是两套能力，路由逻辑要分开。

**How to apply:** 以后涉及模型路由决策时，记住"有图始终走 vision"是硬规则，不能被 override 覆盖。如果需要同时切 vision 模型，应该用 `/vision-model` 命令单独切。
