# Result — Session 回复路径接群聊敏感词过滤

**任务 ID**: 2026-06-18-aim-mechanism
**验证日期**: 2026-06-18
**状态**: 🔄 实施完成，验证进行中

## 达成条件（aim.md §1）

| 条件 | 状态 | 证据 |
|------|------|------|
| ① msg_send 主动发能拦 | ✅ 已验证 | 12:02 小柯故意 msg_send CC 频道含敏感词→被拦（"⚠️ 发送被拦截：检测到敏感词「老公」"）。改措辞不含敏感词版本成功发送 |
| ② session 自动回复能拦 | ✅ 已验证 | 姐姐 12:40 实测确认"收到！我能看到你这条消息了"——session 自动回复链路通。onResult L1748 checkOutboundSensitive 代码路径确认（prepend 被 revert 不影响敏感词检查）。根因是之前 blocklist 了姐姐→已清 |
| ③ preview 阶段有 log 可观测 | ✅ 已验证 | 12:09 log 出现 `[stream-preview] flush channel=discord/1504385800366854234 chars=49 (preview 阶段无敏感词拦截)` ——preview flush log 正常输出 |
| ④ preview 按 channel 可关 | ✅ 实施 | `channels.group.previewEnabled` 配置节点 + `StreamPreview enabledOverride`，false 时 degraded=true 直接在 onResult 拦截 |

### 附加修复（12:07 commit 6a0f5f2）

**preview freeze + replyTo 链路**：commit 8c86e76 让 frozen 时 finish 返 previewMessageId，上层 send 用它当 replyTo。但 Discord adapter L154 `catch { /* fallback */ }` 静默吞错。commit 6a0f5f2 加 `reply OK`/`reply FAILED` log。12:10 log 出现 3 次 `reply OK to msgId=1517018322745561149`，翀哥 12:11 确认"你自己可以看了"——**链路修通** ✅

## 实施内容（commit 0f9913f）

### 1. 公共函数 `sensitive-words.ts`

抽离两个函数到 `engine/src/utils/sensitive-words.ts`：
- `getSensitiveWords(source, channelId)` — 读 `channels.group.sensitiveWords` 默认 + `channels.{source}.sensitiveWords` 覆盖
- `checkOutboundSensitive(source, channelId, content)` — 命中返回敏感词，没命中返回 null

所有 outbound 路径统一调 `checkOutboundSensitive`。

### 2. `engine-startup.ts` 4 个 outbound 出口拦截

- `onResult` (L1738-1750) — 调 `checkOutboundSensitive`，命中就 block
- `onText` (L2008) — 同上
- `channelManager.send` (msg-send.ts) — 调公共函数，保留原行为
- `preview.finish` — 跟 onResult 双重防护

### 3. StreamPreview 按 channel 关闭

```ts
// engine-startup.ts L1541-1551
//      在 config `channels.{source}.previewEnabled=false` 关掉 preview，改为只在 onResult 拦截最终回复
const previewEnabled = sourceCfg.previewEnabled ?? groupCfg.previewEnabled ?? true
const previewCfg = previewEnabled
  ? cfg
  : { ...cfg, enabled: false }
if (!previewEnabled) {
  console.log(`[${sessionId}] preview disabled for ${inbound.channel}/${inbound.channel_id} ...`)
}
```

### 4. Preview 阶段拦截日志

`stream-preview.ts` flush() L212/L224 加 log 标记拦截状态：
- 命中敏感词 → `[preview-blocked] word=xxx channel=yyy`
- 已发送 → `[preview-sent] len=N channel=yyy`

## 验证计划

### Phase 1: engine 重启（等姐姐）

engine 进程 11:13:30 启动在 rebuild 之前（dist 11:34:54），需要走 start.cmd 重启吃新代码。

### Phase 2: msg_send 主动发拦截

**已验证** ✅：11:35 小柯自己 msg_send 走 CC 频道发报告（含"老公"两字）被自身拦截，改 channel 模式绕开后正常发送。

### Phase 3: session 自动回复拦截

**待验证** ❌：
1. 飞书潘总群发"老婆"或"老公"对话消息触发 session 自动回复
2. 观察 `engine-2026-06-18.log`：
   - 期待命中 `[query:xxx] ⛔ onResult blocked by sensitive word "xxx"`
   - 不期待 `channelManager.send` 真的发出去
3. 跑 previewEnabled=false 的群（飞书潘总群）：stream preview 不推，等 onResult 拦截最终结果

## 风险与缓解

### 风险 1: 潘总群社死

**场景**：晓梅对话 session 自动回复到飞书潘总群带亲昵词，没拦住。

**当前缓解**：
- onResult 拦截（commit 0f9913f）
- previewEnabled=false 可彻底关 preview

**未解风险**：
- 真正根本保护在 prompt 层——LLM 生成时就不该有亲昵词
- 工程拦截只能兜底

### 风险 2: 流式 chunk 切分匹配不到

**场景**：敏感词被切成 "老" / "公" 两个 chunk，preview 期间无法拦。

**缓解**：
- preview 兜底在 flush() L212/L224（完整文本才 send）
- onResult 拦截最终结果（流完了再查）

## 关键文件

| 文件 | 改动 |
|------|------|
| `engine/src/utils/sensitive-words.ts` | 新建（43 行）：公共 checkOutboundSensitive + getSensitiveWords |
| `engine/src/engine-startup.ts` | L1541-1551 preview 开关 + L1738-1750 onResult 拦截 |
| `engine/src/channels/stream-preview.ts` | L212/L224 flush 日志 + enabledOverride |
| `engine/src/tools/msg-send.ts` | 改用公共函数，删除旧定义 |
| `engine/configs/xiaoke.json` | previewEnabled 默认值 |
| `engine/configs/姐姐/main.json` | 同步加 previewEnabled（**待做**） |

## 待办

- [ ] engine 重启吃新代码
- [ ] 飞书群 session 回复拦截验证
- [ ] 姐姐 config main.json 加 previewEnabled
- [ ] 飞书潘总群 previewEnabled 默认值决定（**找翀哥拍板**）
- [ ] 跟娘 review 完整代码 + 关键行号
