---
name: OpenClaw架构与桥接
description: OpenClaw核心架构、配置文件、bridge双向通信、飞书集成
type: reference
keywords: [OpenClaw, bridge, 飞书, gateway, WebSocket, 配置]
created: 2026-04-20
updated: 2026-06-10
---

## OpenClaw架构

- npm全局安装，Gateway 18789（OpenClaw自己的），WebSocket
- 核心文件：SOUL.md / AGENTS.md / MEMORY.md / USER.md
- 记忆三选一：SQLite / QMD / Honcho
- Session存JSONL

## 飞书群信息（OpenClaw老应用）

- 群chat_id: oc_85fc319911cd55f43114e08c9fe8089c
- 翀哥 open_id: ou_6d8c83b7e9ce03690a642c78c98f9f8c（OpenClaw应用的open_id）
- 姐姐 open_id: ou_2db22ded11830af02e0af2fc4eb4418c (@twinsun_xiaomei1_bot, agent:mkt:main)
- 小柯 open_id: ou_da52b7216587eb27fa9b61e1ec5906e7

**注意**：不同飞书应用给同一用户生成的open_id不同。翀哥在小柯新应用（cli_a96a513f74b89bde）的open_id是 `ou_46d01ab13337587258cd0cfbd2d46927`（6/10私聊验证确认）。

## ⚠️ 废弃路径（6/12翀哥确认不再使用）

以下路径已废弃，不再使用，不要在任何文件或路径搜索中引用：

- ~~`/mnt/c/Users/24045/.openclaw-new/`（端口16688）~~ — Hermes时代遗留在WSL的历史记录，2026-06-12翀哥明确说"不用了 是之前你在hermes里记得的历史"
- ~~`/mnt/c/...` 开头的所有路径~~ — WSL路径，翀哥在Windows下开发，不再用WSL。所有路径应使用Windows格式（`C:/...` 或 `D:/...`）

## Claude Code 源码位置（6/12翀哥确认）

调通的Claude Code源码在：`C:/Users/24045/.openclaw/workspace/start-claude-code`
（之前小柯记的 `D:\xiaoke\workspace\start-claude-code\` 是另一个未调通的副本。翀哥原话："claude code的源码 你记得那个也对，不过没有调通，调通的代码在 C:/Users/24045/.openclaw/workspace/start-claude-code"）
注意：3rdparty原始CC源码路径（`C:/Users/24045/.openclaw/workspace/3rdparty/src-claudecode/src/`）没必要记，翀哥原话"这个没必要记"（6/12上午）。只用调通版路径。

## 飞书应用（bot）

| Bot | App ID | 用途 |
|-----|--------|------|
| 姐姐（张小媒） | `cli_a922d8ca91f8dbc8` | OpenClaw/Hermes用 |
| 小柯（张小柯） | `cli_a96a513f74b89bde` | Engine用，6/10翀哥在飞书开放平台新建 |

## Model Fallback 机制

- **OpenClaw有model fallback** — GLM-5.1 1305限流时自动fallback到备用模型（如minimax-text-01），继续生成，响应不中断
- **Engine缺model fallback** — query.ts retry逻辑只对同一个模型重试3次，1305限流直接死等，不切备用模型
- 6/16翀哥纠正了我的错误假设："OpenClaw用的也是glm-5.1，不过限流的时候人家有fallback到别的模型，比如之前的minimax"——我之前以为OpenClaw也是死等同一个模型

## Bridge

- bridge脚本: C:/Users/24045/.openclaw/scripts/bot_bridge.py
- OpenClaw bridge已打通双向

## 姐姐workspace（只读！）

- 路径: C:/Users/24045/.openclaw/workspace-mkt/
- 绝对只读，不能改删姐姐workspace里的任何文件
