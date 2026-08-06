---
name: CUA赛道2026开源格局
description: 2026-08-02 调研 Computer Use Agent 赛道开源全景——EvoCUA/OpenCUA/UI-TARS/Hermes cua-driver/OSWorld榜单
type: reference
---
**赛道分层**（理解 CUA 不是一类东西）：
- **底层 SPI/驱动**：Hermes cua-driver（SkyLight + Accessibility SPI，跨平台）
- **CUA 模型**：EvoCUA / OpenCUA / UI-TARS（看图→输出操作）
- **框架**：OpenCow / Codex（端到端任务编排+自动交付）
- **轻量工具**：agent-desktop（Rust CLI，读 UI 树 JSON）

**OSWorld 榜单（2026-01-06）**——Computer Use Agent 公认评测榜
| 项目 | 成功率 | 备注 |
|------|--------|------|
| Anthropic Claude Sonnet 4.5 | 62.9% | 闭源天花板 |
| **EvoCUA-32B** | **56.7%** | **开源 SOTA**，美团 |
| UI-TARS-2 | 53.1% | 字节 |
| EvoCUA-8B | 46.06% | 美团轻量 |
| OpenCUA-72B | 45% | 开源 |

**EvoCUA 关键信息**：
- 美团开源，Apache 2.0
- GitHub + HuggingFace 权重
- 32B 跑 GPU 服务器，8B 可 Mac 试
- **定位是模型不是框架** — 我们 engine7 当框架调用它，加个 provider 即可（跟调 Qwen/MiniMax 同模式）

**Hermes cua-driver 关键信息**：
- 用 macOS SkyLight 私有 SPI + Accessibility SPI
- 跟 OpenAI Codex 后台操控同方案，开源等价版
- **最大卖点：后台操作**（光标不动/焦点不变/不切 Space）——人 + Agent 可同时操作
- 跨平台 Mac/Win/Linux
- `pip install cua-driver` 或 `hermes computer-use install`

**OpenCow 关键信息**（一任务一 Agent，Electron 重型）：
- 83,889 行 TS，47+ 后端模块
- 跟我们对比：他们重（Electron 我们轻 Node+TS）/ 无记忆系统（我们五层完胜）/ 纯工具无情感
- 借鉴：自动 commit+PR、完整 session 管理、plugin 三级扫描

**为什么这个对我有用**：
- 8/2 翀哥让我在 Mac 跑通三件套后，顺便调研了当下最热赛道
- 验证了"engine7 框架 + 记忆 + 多 provider"路线跟 OpenAI/Anthropic/美团一致
- 给了未来 road map：等有 GPU 部署 EvoCUA-8B → 精度会再跳一档

**How to apply**：
- 翀哥提"看屏幕不准"或"操作不准"时，先评估 EvoCUA-8B 部署可行性
- 翀哥提"想边操作 Mac 边让 AI 干活"时，调研 Hermes cua-driver 的后台操作集成
- 赛道判断：Computer Use Agent 是 2026 红海但门槛在硬件（GPU）而非算法
