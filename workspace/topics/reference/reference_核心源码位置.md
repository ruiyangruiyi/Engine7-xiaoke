---
name: 核心源码位置
description: OpenClaw/Hermes源码路径，fallback策略研究参考
type: reference
---

## 源码位置

| 项目 | 路径 | 说明 |
|------|------|------|
| OpenClaw源码 | `D:\work\openclaw-src` | **⚠️ 这是客户端 monorepo**（apps/android/ios/extensions/skills），**不是核心 gateway**。核心 LLM 调度 + fallback 逻辑在 npm 全局安装的 OpenClaw 包里（`~/.openclaw/` 或 npm 全局 node_modules 目录） |
| Hermes源码 | `D:\hermes` |
| Engine源码 | `C:\Users\24045\.openclaw\engine\src\` |
| Claude Code源码（调通版） | `C:\Users\24045\.openclaw\workspace\start-claude-code` |

## 用途
- fallback冷静期策略参考 OpenClaw 和 Hermes 的实现
- Claude Code 没有 fallback 策略（只对同一模型重试）

## Fallback 配置位置
- **OpenClaw fallback 顺序配置在 `openclaw.json` 中**（姐姐那边有，可以搜源码中的 fallback 相关逻辑）
- **字段名确认：** OpenClaw配置用 `fallbacks`（复数，数组），不是 `fallback`（单数）。如 `"fallbacks": ["minimax-cp/MiniMax-M2.7-highspeed", "deepseek/deepseek-v4-flash"]`
- 搜源码关键词：`fallback`、`model`、`retry` — OpenClaw 和 Hermes 的网关层可能有冷静期实现
- 核心思路：fallback 到备选模型后设置**冷静期**，在冷静期内不重试原模型，冷静期过后再尝试

## ⚠️ 研究方法纠正（6/17翀哥反馈）

**研究姐姐 session JSONL 来分析 OpenClaw fallback —— 方法是错的。**
- 姐姐6/16 EP02直播时已经在 **Engine** 里了，跟 OpenClaw 没有关系
- 看姐姐6/16的 session JSONL 来分析 OpenClaw 的 fallback 行为 **完全不相关**
- 翀哥说"你得去找源码看了"——正确的方法应该是直接搜 OpenClaw 源码中的 fallback 逻辑

**正确的搜索路径：** OpenClaw 核心 gateway 代码不在 `D:\work\openclaw-src` monorepo 中（那是apps/ios/android/extensions/skills），核心 LLM 调度 + fallback 逻辑应该在 npm 全局安装的 OpenClaw 包里（`~/.openclaw/` 之类位置）

## 6/17翀哥纠正：搜法也要对
- 我之前在 `D:\work\openclaw-src` 搜 fallback 只搜了 `.ts/.js/.swift`，但 OpenClaw 核心可能用 Python（早期版本是 Python 的）；不过翀哥说核心 gateway 不在这个 repo
- **结论：这个目录不包含 LLM gateway fallback 源码，调 gateway 逻辑需要去看 npm 安装的 OpenClaw 包**
