# Bot循环防护最终调试 (2026-05-27 21:00-23:00)

## 问题
stripMentionIds改了还是循环——CC和TestEngine互刷不停

## 调试过程

### 尝试1: ignoreUserIds入站屏蔽
- engine-config.json加`ignoreUserIds: ["1504373837880627280"]`
- discord.ts handleMessage加`if (msg.author.bot && this.config.ignoreUserIds?.includes(msg.author.id)) return`
- 结果：**没生效**，CC消息还是进来了

### 尝试2: debug日志定位
- 加`console.log('[debug] ignoreList=', this.config.ignoreUserIds, 'author=', msg.author.id, 'bot=', msg.author.bot)`
- 日志显示`ignoreList=undefined`
- **根因**：manager.ts `loadFromConfig()` 构建DiscordAdapter时没传ignoreUserIds参数
- 修了manager.ts加`ignoreUserIds: config.discord.ignoreUserIds` + ChannelConfig类型加字段

### 尝试3: ignoreUserIds生效了但太激进
- CC bot所有消息被拦，包括@TestEngine的
- 改为：没@TestEngine时才忽略（`if (!msg.mentions?.has(client.user?.id || ''))`）
- 结果：cc-connect的mentionBatcher给所有出站自动加@mention → isMentioned永远true → 例外永远生效 → 又循环

### 最终方案: stripMentionIds复用做入站拦截
- 删掉ignoreUserIds，用stripMentionIds同时做入站+出站
- 入站：`msg.author.bot && this.config.stripMentionIds?.includes(msg.author.id)` → 无条件丢弃，不判断isMentioned
- 出站：`if (options?.replyTo) stripBlockedMentions(message)` → 只在reply时剥
- CC bot被无条件拦截没问题（CC走cc-connect内部通道）
- **测试通过**：循环断了，小柯消息正常通过

## 关键代码位置
- `channels/discord.ts` handleMessage — 入站拦截
- `channels/discord.ts` send() — 出站剥离（条件：replyTo时）
- `channels/manager.ts` loadFromConfig() — 配置透传
- `engine-config.json` channels.discord.stripMentionIds

## 教训
1. 配置透传必须完整——manager.ts漏一个字段就是undefined
2. cc-connect的mentionBatcher会自动给所有出站加@mention，isMentioned判断不可靠
3. 防循环需要无条件丢弃，不判断mention状态
4. debug日志是定位config加载问题的最快方式
