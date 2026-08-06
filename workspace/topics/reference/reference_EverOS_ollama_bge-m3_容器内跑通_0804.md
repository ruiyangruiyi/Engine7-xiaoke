---
name: EverOS ollama bge-m3 容器内跑通+CPU测速
description: 2026-08-04 凌晨在 EverOS Docker 容器内装 ollama + bge-m3 并测速，CPU 443ms/条够用
type: reference
---

2026-08-04 凌晨 00:00 在 EverOS Docker 容器内装 ollama v0.32.5 + bge-m3 跑通。

**CPU 性能数据（容器内实测）：**
- 冷启动（模型加载）：1.8s
- 单条热路径：**443ms**
- batch 10：132ms/条

跟翀哥之前估的一致（300-500ms/条），CPU 完全够用。

**关键验证：**
- bge-m3 输出 **1024 维** ✓（跟 LanceDB schema 一致）
- ollama 在容器内跑，EverOS 容器能通过本地网络访问 ✓

**安装踩坑：**
- ollama v0.32.5 tar.zst 里 `llama-server` 在 `/usr/local/lib/ollama/`，ollama 不搜那个路径
- 解压后建符号链接到 ollama 默认搜索路径才跑起来

**Why:** 翀哥要切本地 embedding 省 API 钱 + 摆脱远程 embedding 限制；bge-m3 是 1024 维多语向量模型，LanceDB 现有 schema 兼容。

**How to apply:** 切到本地 bge-m3 后，re-embed 全部 487 条记忆用时 ≈ 1 分钟（487 × 132ms）。导入完成后切，否则中途切换要处理 dim 不一致 + 部分文件已灌的问题。