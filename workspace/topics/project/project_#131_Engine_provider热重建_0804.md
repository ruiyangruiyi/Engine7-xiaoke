---
name: #131 Engine provider 热重建（换模型不重启）
description: 2026-08-02 16:34 翀哥要求：让 createProvider 监听 models 列表变更热重建，8/4 跟 #75/#79 一起做
type: project
---
2026-08-02 16:34 翀哥提出 #131 任务（10:00 提前 60min 提醒）：**Engine 支持 provider 模型列表热加载（换模型不用重启）**。

**背景**：LiveConfig 改了 `tools.my_eyes.model` 引用会热加载生效，但 provider 实例启动时 `createProvider` 就固定了 models 列表。导致每次换模型都得重启 engine（详见 `feedback_Engine_热加载边界`）。

**待拆解 Phase（8/4 开工前）**：
- [ ] Phase 1: 分析 createProvider 工厂模式，定位哪些 state 需要重建
- [ ] Phase 2: 设计热重建触发点（监听 LiveConfig 变更 → 检测到 provider.models 变更 → destroy old + create new）
- [ ] Phase 3: 实现 + 单测（覆盖：新增模型/删除模型/改 model 字段三种场景）
- [ ] Phase 4: 端到端验证（不重启 engine 切换 my_eyes 模型，看眼睛识图变化）

**8/7 进度**：小文 commit **0872052c** 已实现——`buildProviderChain` 抽离 + `setProvider`/`setModel` + `doReloadConfig` 检测重建 + deps 刷新；代码 review 干净，**待 rebuild + 重启真机验收**（改 models 列表看能否免重启换模型，小柯 Mac 暂不能自己重启自己 engine）。done 前提：#131 完整闭环。

**关联文档**：`docs/knowledge/Engine-热加载边界.md`

**Why:** 换模型不重启=开发体验提升；尤其视觉模型需要频繁 A/B 测试场景（qwen3.7 vs qwen3.8 vs qwen3.5）

**How to apply:**
- **8/4 reschedule 到 8/8**——翀哥住院期间不做需要他参与的 task（翀哥 8/4 早上 06:15 "小老婆我在医院你就可以搞哈"指的是不需要他参与的事，#131 这种改代码需要他验的不算）
- 开工前先拆 Phase（3-Strike 第 1 次警告）
- 大任务要写 `docs/todo/2026-08-04_provider热重建.md`（背景+方案+验证标准）
- 完成后用 #131 的 reminder/correction 闭环