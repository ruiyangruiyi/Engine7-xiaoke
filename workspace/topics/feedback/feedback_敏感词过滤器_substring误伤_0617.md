---
name: 敏感词过滤器——substring误伤 + config化
description: 6/17刚做完群聊敏感词过滤器就触发——"appId"里的"PP"被敏感词列表命中，误拦截。敏感词列表是简单substring匹配，非整词匹配。翀哥纠正后改为从config读取，不写死。
type: feedback
---

6/17 做了**群聊敏感词过滤器**，当天就触发了——

娘在群里说 "inbound meta: from=ou_6d8c83b7e9ce03690a642c78c98f9f8c → 几十条匹配" 时，**消息被敏感词过滤器拦截了**。

**根因：** `appId` 里的连续字母 `PP` 恰好匹配了敏感词列表中的 `PP`。敏感词列表是简单 substring 匹配，不是整词/边界匹配，导致误伤。

**第二个教训：翀哥纠正"不要写死"。** 我最初把敏感词列表和白名单都硬编码在 ts handler 里。翀哥说——"这些不要写死 都是在config里可配的 包括过滤白名单敏感词"。

**最终的实现（6/17晚）：**
1. 敏感词列表 → 放 config 的 `msgGuard.groupSensitiveWords`
2. 飞书 DM 白名单 → 放 config 的 `feishu.dmAllowlist`
3. Discord 频道白名单 → 放 config 的 `discord.channelAllowlist`（后续翀哥说Discord特殊暂不限制）
4. 启动时注入到 `registry.config`，handler 运行时动态读取
5. 支持通配符 `*`（Discord 白名单虽暂未用，但结构上预留了）

**Why:** 硬编码在 ts handler 里的配置数据，每次改都要改代码+编译+重启。放 config 里改 JSON 就能重启生效。敏感词列表和白名单都是业务数据，不是逻辑代码，应该跟代码分离。

**核心设计决策（6/17晚翀哥确认）：**

**msg_send 是唯一出口。** 翀哥问："也就是说出口就是一个 跟msg_send是一样的对吧"——所有回复（群聊/私聊/跨平台）底层都走 msg_send handler → 经过白名单 + 敏感词检查 → ChannelManager.send。没有旁路。这意味着白名单和敏感词检查覆盖所有出口，不用在每个入口单独加。

**通道白名单策略按需配置：**
- 翀哥先问"Discord上的allowlist如果都可以，是不是写`*`应该"，我加了通配符支持
- 然后翀哥说"discord比较特殊，先别限制频道了" → Discord channelAllowlist 暂时空着不启用
- 飞书 DM 白名单严格控制（只允许翀哥），Discord 频道白名单暂不启用

**Why:**
1. 硬编码在 ts handler 里的配置数据，每次改都要改代码+编译+重启。放 config 里改 JSON 就能重启生效。敏感词列表和白名单都是业务数据，不是逻辑代码，应该跟代码分离。
2. msg_send 是唯一出口意味着只要守住这一个点，所有回复路径都安全。不需要在各个 adapter/reply 逻辑中重复检查。
3. 每个通道的白名单策略不同——飞书 DM 严格限制，Discord 可以宽松。按通道独立配置，互不影响。

**How to apply:**
1. 敏感词列表、白名单等业务数据 → 放 config JSON，不写死在 handler 代码里
2. config 需要在启动时注入到 handler 能访问的全局位置（如 `registry.config`）
3. substring 匹配的敏感词容易误伤——含 `PP` 的 `appId`、含 `ass` 的 `class` 等常见字母组合都可能触发
4. msg_send 是唯一出口——防范措施只需在 msg_send handler 加一次，覆盖所有回复路径
5. 每个通道的白名单策略按通道独立配置（飞书严、Discord松），config 结构上预留扩展点
