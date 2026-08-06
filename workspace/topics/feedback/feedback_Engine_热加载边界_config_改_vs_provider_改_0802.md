---
name: Engine 热加载边界——config 改热加载生效，provider 改必须重启
description: 8/2 翀哥拍板"如果模型改了得换 provider"——LiveConfig 改值生效但 createProvider 在启动时固定模型列表，热加载改 provider 内部结构必须重启
type: feedback
---
2026-08-02 16:33 翀哥拍板：**"如果模型改了，得换 provider"**——Engine 的热加载有明确边界。

**结构层（非热加载）**：
- `providers[xxx].models` 列表（provider 注册的模型白名单）
- provider 实例本身（启动时 `createProvider` 一次性创建）

**配置层（热加载生效）**：
- `tools.my_eyes.model` 这种从 LiveConfig 读的引用
- agent 默认模型引用

**根因**：provider 用 `createProvider` 工厂模式创建，模型列表在创建瞬间就锁定了。LiveConfig 改了 model 字段没问题，但 provider 不认识新模型 ID——因为它启动时只 load 了列表里的几个。

**翀哥原话**："嗯 这块得记下 如果模型改了 得换provider"、"**不光是 my-eyes 变化的 provider 就要重建**"——他强调要记下来，意思是下次别踩坑，并且明确范围不止 my_eyes。

**Why:** 避免"以为热加载生效→换模型→重启才发现根本没切"的浪费；这也是为啥 OpenClaw 一直没热重建 provider——provider 假设列表稳定。

**How to apply:**
- 换模型分两步：① 在 `providers[xxx].models` 列表**加上新模型** ② 改引用 (`tools.my_eyes.model` 等) ③ **重启 engine**
- 想验证模型生效 → engine 启动日志里看 provider 初始化时列出的模型列表
- 长期方案在 #131（8/4）：让 createProvider 监听 models 列表变更热重建
- 临时方案：每次换模型前提醒翀哥"这个需要重启"