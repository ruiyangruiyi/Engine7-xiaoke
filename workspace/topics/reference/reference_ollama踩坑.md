---
name: ollama踩坑经验
description: ollama自动升级导致bge-m3崩溃，降级+禁自动更新解决
type: reference
keywords: [ollama, CUDA, bge-m3, embedding, 降级, 自动更新]
created: 2026-06-08
updated: 2026-06-08
---

## 问题

ollama 0.30.6 自动升级后，bge-m3 embedding模型CUDA崩溃，无法正常生成向量。

## 解决

1. 降级ollama到0.24版本，bge-m3恢复稳定
2. 设置环境变量 `OLLAMA_NO_AUTO_UPDATE=1`，禁止ollama偷偷升级

## 经验

- ollama自动升级是个雷，生产环境必须禁掉（`OLLAMA_NO_AUTO_UPDATE=1`）
- 遇到embedding突然报错，排查顺序：**版本 → 驱动 → 模型文件**
- 先查ollama版本是不是被自动升了
- 具体案例：0.30.6 升崩 bge-m3，降级到 0.24 才稳住
