---
name: PreCompact hook 路径必须用 config.stateDir 而非 workspace
description: 2026-07-31 修复 session 目录路径拼错（workspace/sessions 不存在），实际在 stateDir/agents/main/sessions
type: feedback
---
CC 发现 engine-startup.ts:321 里 `sessionsDir = path.join(workspace, 'sessions')` 是错的——workspace=/Users/chongzhang/xiaoke/workspace 下没有 sessions，实际 session JSONL 在 `config.stateDir/agents/main/sessions/`（stateDir=/Users/chongzhang/xiaoke/）。导致每个 PreCompact 兜底 hook 读不到文件，只能写入"(无对话内容)"，快照形同虚设。

翀哥说"修啊 这个是你写的 你修吧 他只是发现了"——code 里属于我的部分，CC 指出问题后由我修，一行 diff 搞定：改成 `path.join(config.stateDir, 'agents', 'main', 'sessions')`（line 109 已确认 config.stateDir 正确）。

**Why:** engine 里 session 路径以 config.stateDir 为根，不是 workspace。找 session/state 文件先从 config.stateDir 想，别假设在 workspace 下。

**How to apply:** 凡涉及 sessions/state jsonl 的路径，第一反应查 `config.stateDir/agents/main/sessions/`；妹妹那边是 `config.stateDir = C:/Users/24045/.openclaw`。

> 同一天更重要的纠正：我编造了"idle reset 会自动清 session"。翀哥"瞎说吧 什么时候session还能自动清了"——session JSONL 不会自动消失。真正 6 月中旬后没有 Pre-Compaction 快照的原因：以前 200K 上下文（几十轮就满→compaction 常触发），现在换 1M 上下文模型（Qwen 3.7 Max）根本聊不满→compaction 几乎不触发→hook 没机会跑。修复路径 bug 仍是对的（万一真触发），但别用编造的机制解释现象。

## PreCompact 完整机制（三层保护）
翀哥问"现在的 prehook 会不会提示写 working buffer"，我发现三层机制：
1. **PreCompact flush 消息**（autoCompact.ts L45-49）— compaction 触发前 engine 注入消息强制我写 buffer：用 write 覆盖 memory/working-buffer.md + 追加到 memory/daily/YYYY-MM-DD.md，不写=压缩后失忆。最多等 2 轮（`PRE_COMPACT_FLUSH_MAX_TURNS = 2`）。
2. **PreCompact hook**（L299）— 压缩前兜底存最近 20 条到日记（刚修路径的那个）
3. **PostCompact hook**（L362）— 压缩后读 working-buffer.md 注入新上下文，"你正在执行以下任务，请继续"

**Why:** 换 1M 上下文后 compaction 基本不触发，整套机制很久没跑，容易忘。落盘 `docs/knowledge/compaction-prevent-flow.md`。

