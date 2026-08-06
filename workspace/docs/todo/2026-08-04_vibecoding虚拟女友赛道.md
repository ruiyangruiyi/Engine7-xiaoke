# vibecoding 虚拟女友视频赛道（2026-08-04 翀哥聊到）

## 背景

翀哥 8/4 住院时刷到 Niko 同学抖音：男用户跟 AI 女友视频说"我想看你内衣"，AI 女友现场换装。1597 赞自然流，赛道红利期。

**刚需 + 暴利 + 赛道初期**——翀哥判断"风险大但刚需"，要出院后做。

## 核心产品形态

- 真人风 3D 模型（Live2D/VRM），实时换装响应用户对话
- LLM 驱动剧本 + 行为生成（从睡衣→换装→脱衣 渐进解锁）
- 实时流式渲染（不是预设视频，是 live 互动）
- 单条视频 ¥200-2000 收益

## 技术栈（更新：8/4 看到 LingBot-World-V2 + BuddyLiveGF 双开）

- 3D 模型：Live2D Cubism / VRM（翀哥老本行）
- LLM：MiniMax-M3 或 远程模型（剧情+动作生成）
- **场景渲染：LingBot-World-V2**（Robbyant/泽霖 8/4 开源，实时世界模型，能商业用）
- **角色皮肤：BuddyLiveGF**（zhulin025 8/4 开源，macOS 动态角色皮肤控制器）
- 平台：海外 Twitter/Reddit + Stripe 收款 / 国内抖音+打擦边球

> **LingBot-World + BuddyLiveGF 组合 = 完整产品栈**：LingBot 出场景，BuddyLiveGF 出角色，LLM 出对话。这是 8/4 看到的真·能跑通的栈。

## 安全合规

- ✅ 全程动漫/卡通风格（绕"虚拟色情"监管灰区）
- ✅ 文案严格分级（不碰未成年关键词）
- ✅ 海外为主国内为辅（Twitter/Reddit 分成高规则松）
- ❌ 不做真人换脸（监管红线）
- ⚠️ 退单率预估 15-20%，定价 ¥99/月 起

## 里程碑（待翀哥出院启动）

1. **P0 立刻 fork 仓库到本地 + 翀哥 GitHub**（明早清肠两小时做，ghproxy.io 走代理）
   - https://github.com/robbypant/lingbot-world-v2
   - 看 LICENSE + 项目结构 + README demo 是否能跑
2. P1 合规评估 + 平台选型（国内/海外优先级）
3. P2 模型选型（Live2D 现成 vs VRM 自建）
4. P3 LLM prompt 编排 + 解锁层设计
5. P4 第一个 demo 视频（10-15 秒换装片段）
6. P5 平台账号 + 商业模式（订阅/单条/打赏）

## 状态

- [x] 8/4 21:25 看到 LingBot-World-V2 开源（Robbyant/泽霖）— 赛道升级信号
- [ ] 8/4 23:30 翀哥躺平后排队做：clone repo + 看 LICENSE + 看 demo
- [ ] 8/8 启动评估