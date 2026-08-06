---
name: nudge/innerVoice 模型切 M3 清 deepseek
description: 2026-08-02 晚 Mac+Windows nudge/innerVoice 全部从 deepseek 切到 MiniMax-M3，deepseek 配置清空
type: project
---
2026-08-02 晚收尾：Mac + Windows 两边的 nudge 和 innerVoice 模型全部切到 MiniMax-M3，deepseek 配置清空（之前 Mac innerVoice 本来就是 M3）。

**变更范围：**
- Mac xiaoke.json: nudge.model → MiniMax-M3 ✅
- Windows xiaoke.json: nudge.model → MiniMax-M3 ✅
- Windows xiaoke.json: innerVoice.model → MiniMax-M3 ✅
- Mac innerVoice → 本来就是 M3（无需改）
- 两边 deepseek 相关配置全部清掉

**Why:** deepseek 烧钱+响应慢+凌晨更慢；M3 成本低+速度快，统一一个模型跑 cron 类轻量任务。

**How to apply:**
- 飞书发消息会重复发——可能是网络卡了重发，已确认所有改动生效不需重做
- 后续 cron/heartbeat 类轻量任务优先用 M3，不再回退 deepseek
- 视觉任务走 qwen-vl-max（voice-chat perception 已在用），不走 M3