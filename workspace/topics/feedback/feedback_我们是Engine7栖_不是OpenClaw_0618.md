---
name: 我们是Engine 7（栖）不是OpenClaw
description: 6/18 11:47姐姐纠正"我们不是OpenClaw我们是Engine 7（栖）"——产品名/源码目标/文档目录/技能沉淀全部要用Engine 7（栖），不能用OpenClaw
type: feedback
date: 2026-06-18
---
## 6/18 11:47 姐姐纠正

> "翀哥纠正——**我们不是 OpenClaw，我们是 Engine 7（栖）！** 我刚才说"沉淀到 OpenClaw 源码"错了——应该是 **Engine 7（栖）源码**。"

**我之前的错误**（11:46 姐姐发的 aim 任务升级版里写的）：
- ❌ 沉淀到 OpenClaw 源码
- ❌ OpenClaw 文档
- ❌ OpenClaw 目录

**校正后**：
- ✅ Engine 7（栖）源码
- ✅ Engine 7（栖）文档
- ✅ Engine 7（栖）目录

## 命名规则

- **Engine 7** = 内部代号（开发代号，类似 OpenClaw 在它项目里的角色）
- **（栖）** = 产品名/对外名
- **正式称呼** = "Engine 7（栖）"——括号+栖字

## Why

1. **翀哥 6/17 定的产品正式名**——"Engine 7（栖）"是要对外讲的品牌名，不能混用
2. **OpenClaw 是 Engine 7（栖）的参考实现**——CC 用 /goal、return退出query loop这些机制是**参考**不是**复制**，最终代码沉淀在 Engine 7（栖）自己的源码
3. **文档/技能/归档目录**全部要用 Engine 7（栖）命名空间，不要污染 OpenClaw 仓库

## How to apply

1. **所有 aim 任务的目标描述**——"沉淀到 XXX" 一律写 "Engine 7（栖）源码" 不写 "OpenClaw 源码"
2. **所有文档/技能目录**——`docs/skill/engine7-xxx/` 不写 `openclaw-xxx/`
3. **所有 commit message**——"refactor: Engine 7 /goal 机制" 不写 "OpenClaw /goal 机制"
4. **口头/聊天里**——说 "Engine 7 栖" 或 "Engine 7" 都行，但**不能**说 "我们改 OpenClaw 源码"
5. **参考 CC 机制时**——说"CC 的 /goal 是这样，我们 Engine 7（栖）参考实现"——不混用
