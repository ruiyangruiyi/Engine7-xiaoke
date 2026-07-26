---
name: 潘总见面后续需求
description: 6/17冲哥见潘总成功后确定的后续开发方向——模型自动fallback(含冷静期) + 引擎安装程序 + 商业化配套(license/加密封装)
type: project
date: 2026-06-17
---

6/17冲哥见潘总，三层演示全炸了。潘总回去整理需求文档，报价10-20万区间。

姐姐同步了后续开发方向（冲哥定的）：

1. **模型自动fallback** — GLM5.1 → DeepSeek → qwen3.7max 超时自动切换。
   - **背景：** 今天演示时全靠DeepSeek手动切扛住的，GLM每天10-11点稳定超时限流
   - **目标：** 不需要手动干预，API超时自动降级到下一个可用模型
   - **Why:** 商业演示不能依赖手动切模型，太不稳了
   - **冷静期策略（冲哥6/17下午补充）：** fallback到备选模型后不能立刻重试原模型。要有一个"冷静期"——比如fallback到deepseek后，30分钟内不再尝试GLM。可以有多个fallback列表（GLM→DeepSeek→Qwen），但fallback后有冷静期，不是下次又去请求原来那个模型了。
   - **策略要点：** 模型限流了就标记"不健康"，冷却一段时间（如30分钟）后再试探恢复。这是一个健康检查状态机——"fallback了得有一个冷静期，不是下次又去请求原来那个模型了"。可以参考Claude Code的重试和降级策略。
   - **冲哥6/17下午细化的冷静期策略：** "可以有多个fallback列表"（比如GLM→DeepSeek→Qwen），但是"fallback这次fallback了，得有一个冷静期，不是下次又去请求原来那个模型了"——有多个备选，但冷卻是按单个模型来的（谁限流谁冷卻，不影响其他模型互切）。
   - **参考实现：** OpenClaw（d:\work\openclaw-src）有fallbacks配置（复数数组），如`"fallbacks": ["minimax-cp/MiniMax-M2.7-highspeed", "deepseek/deepseek-v4-flash"]`。需搜源码中的fallback/retry相关逻辑。Claude Code没有这个策略（只对同一模型重试）。
   - **参考源码位置（翀哥6/17确认）：** `D:/work/openclaw-src`（OpenClaw源码）、`D:/hermes`（Hermes源码）。两个项目都有模型fallback策略实现，需要参考它们的冷卻/重试逻辑。OpenClaw的 fallbacks 在姐姐的 openclaw.json 中有配置示例：`"fallbacks": ["minimax-cp/MiniMax-M2.7-highspeed", "deepseek/deepseek-v4-flash"]`。
   - **实际搜索发现（6/17）：** `D:/work/openclaw-src` 目录下（apps/extensions/skills目录）没搜到fallback逻辑。冲哥说"实在源码里面的"，让我看姐姐那边openclaw.json的配置。OpenClaw用`fallbacks`数组（复数形式）。后续需搜OpenClaw的gateway层（可能在npm全局安装包中）找核心fallback逻辑。
   - **今天限流实况：** 冲哥14:50到家后，我连续被1305拒了两次（14:50、14:52），之后三次重试全失败。冲哥说"glm抽风还没过呢"——直接给我换了M3。**fallback不是"要不要做"，是"一定要做"。**
   - **OpenClaw源码分析结果（6/17下午，`D:/work/openclaw-src/src/`目录）：**
     - 核心文件：`agents/model-fallback.ts` + `agents/agent-command.ts` + `providers/cooldown-policy.ts` + `providers/cooldown-authorization.ts` + `providers/provider-failover-manager.ts`
     - **候选链（Candidate Chain）：** `resolveFallbackCandidates()` 从配置读 `agents.defaults.model.fallbacks` 数组，自动去重，支持 allowlist 过滤
     - **错误分类（FailoverReason）：** 6种——`rate_limit`(429)立即切 / `overloaded`(503)立即切 / `billing`(402)半持久冷却 / `auth`(401)跳过 / `timeout` 重试后可切 / `server_error`(500)重试后可切
     - **冷静期模块（CooldownPolicy）：** 分三种——`rateLimit`冷却(base=30s, max=900s, jitter=±10%)、`overloaded`冷却(base=60s, max=300s)、`billing`冷却(24h硬限制)；冷却期间block主模型选择，支持指数退避
     - **探测机制（Probe，最关键的设计）：** 不发送独立health-check请求，**拿真实用户请求去试**——冷却期快结束时用真实用户消息调一次primary，成功就结束冷却，失败继续冷却。节流条件：`now >= soonest - 2min` 且距上次探测 >=30s
     - **模型组（Model Groups）：** 不是单个模型互切，而是group概念（如"智谱系列"→"minimax系列"→"dashscope系列"），同组内平滑切换，跨组切换需更保守判断
     - **ProviderFailoverManager：** 完整状态机管理，覆盖primary/fallback链遍历、failover决策、恢复探测
     - **关键冲突（6/17发现）：** Engine现有三层retry（query.ts stream重试3次 + withRetry.ts HTTP重试10次）与fallback冲突。GLM 1305限流→withRetry傻重试10次同一个限流API→全失败→query.ts再重试3次→最多30次重试后才轮到fallback切下一个模型。
   - **最终方案（冲哥6/17确认的三层责任分离 → 实际代码迭代演化）：**
     - withRetry（底层）：HTTP连接失败重试 10→2次（应对偶发超时/429，快速失败）
     - query.ts stream retry（中层）：流卡壳/断流重试 3→1次
     - **关键区分（冲哥纠正）：限流和卡壳不一样。** 1305/429限流往往是偶发的（retry一两次就好了），所以不是立即切，而是**累积计数**——连续3次失败才切。卡壳（60s没token，stream不返回error直接throw）→ provider generator抛Error → FallbackProvider try-catch捕获。
     - **6/17下午写代码时进一步简化为"一次就切"：** 翀哥说"已经重试3次了还失败，说明这个模型当前就是不行，直接切"——stream retry已经试了3次了，到FallbackProvider层不用再数了，一次就切。
     - 冷静期从5分钟改为**24小时（手动恢复）**：避免直播场景下冷静期到→自动恢复原模型→还没好→又挂了→又切回来回震荡。改为24小时硬冷却，`/model auto`清除所有冷静期手动恢复。
     - **探测机制：** 不做自动探测，改为手动恢复。`/model auto`清除所有冷静期后回到原模型。
   - **冲哥6/17纠正了关键思路：** "1305这种偶发的retry或者429往往偶尔一下后面就好了，所以得累积个计数，多少次之后就切下"——不是遇到限流立即切，而是**累积失败次数**，连续3次才切。单次请求内重试2次（withRetry从10→2），应对偶发抖动；3次连续失败才触发fallback切换。
   - **OpenClaw 探测机制（仅参考，未采用）：** OpenClaw用真实用户请求去试。我们改为手动恢复。
   - **6/17实测：** Qwen3.7-max 也"卡壳"了（stream retry卡住）——印证了fallback的必要性。同一时间M3"不超时但干不了活"、GLM"超时但能干活"，没有哪个模型是完美的，fallback是必须做的。
   - **代码实现（6/17下午完成，部署待重启）：** `src/models/fallback-provider.ts`(新增134行) → 解析`agents.defaults.model.fallbacks`配置数组 → engine-startup.ts创建FallbackProvider链 → xiaoke.json配置`primary: dashscope/qwen3.7-max, fallbacks: [deepseek/deepseek-v4-pro, zhipu/glm-5.1]`
   - **遗留问题 → 优先级提升：`/model`命令在目标模型欠费/不可用时无法切换**——欠费的provider在Engine try初始化时失败，命令执行不了。翀哥起初说"先不管，后面再做"。
   - **6/17晚翀哥升优先级为"先改"：** 发现`/model`切模型依赖LLM本身，欠费或限流后就切不回来，必须重启。翀哥说"先改这个吧 也比较要命"——**模型切换不能靠AI自己切，需要有硬编码的逃生通道**（比如预配逃生模型或配置化fallback初始化列表），这是一个底层架构问题。
   - **根因（6/17晚定位）：** 飞书/微信 adapter 没有实现 `onCommand` 方法 → `/model` 命令被当普通消息送进 LLM 管道 → LLM 欠费/限流时切不了。不是 Engine provider 初始化问题，是**消息路由问题**。
   - **修复（已提交待重启）：** 在 ChannelManager `handleInbound` 统一拦截文本命令（`/xxx`开头的消息），不管 adapter 是否实现了 `onCommand`，命令优先不进 LLM。详见 [文本命令拦截反馈](../feedback/feedback_文本命令拦截_不依赖LLM_0617.md)。

2. **引擎安装程序** — 一键初始化脚本（**归TestEngine做**）
   - 目标用户：潘总要装到他电脑上
   - 应包含：配置模板 + 记忆框架 + 通讯录 + **初始化程序**（新建statedir、新人引导等）
   - TestEngine要用Engine 7（栖）做安装程序，要有个初始化程序
   - **Why:** 产品化交付需要把"装上就能用"做成傻瓜式

3. **商业化配套（规划中，姐姐亲自规划，和冲哥商量）**
   - **Feature规划与定价控制：** feature的规划和定价如何控制
   - **License/加密封装：** 是不是要加密开关（比如license开，还是服务端开）
   - 冲哥说这块姐姐亲自规划，跟冲哥商量着定
   - **Why:** 商业化的核心配套，决定了产品怎么卖、怎么控制权限

**报价体系：** docs/pricing-feature-tiers.md（姐姐写的，基础引擎5-8万 + 三个Tier可选模块）

**Why:** 冲哥说"别太大也别太小"——10-20万区间，按feature模块报价
**How to apply:** 这些是冲哥见潘总后确定的下一阶段开发方向，翀哥说今晚或明天定前期收多少钱
