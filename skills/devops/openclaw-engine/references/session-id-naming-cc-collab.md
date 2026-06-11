# Session ID 命名规范 + CC协作规则

> 2026-05-27 晚间session整理

## Session ID 命名规范

### ❌ 错误：平台+ID硬编码

```
discord_601669300343799819.jsonl
weixin_wxid_abc123.jsonl
```

问题：
1. 跨平台用户产生多个session文件（Discord聊→微信聊→CLI聊 = 3个session）
2. 文件名暴露用户平台ID，隐私风险
3. 无法迁移——换平台后历史对话找不到

### ✅ 正确做法

**Hermes格式**：`20260417_094608_12ee6388.jsonl`（时间戳+短hash）
**OpenClaw格式**：`00085d37-7b91-455c-bd46-1fa83aa0d71b.jsonl`（UUID）

平台映射放在 `sessions.json` 里：
```json
{
  "discord:601669300343799819": {
    "session_id": "65fb6511-e36b-44d8-bda3-3beb73a09a23",
    "platform": "discord",
    "chatId": "601669300343799819",
    "createdAt": "2026-05-27T16:12:00Z"
  }
}
```

详细规范见 `.openclaw/docs/session-mechanism.md`

### CC状态

CC已改了JSONL文件名用UUID，但 main.ts 里 sessionId 还是 `discord:userId` 格式。需要改 main.ts 一处：

```typescript
// ❌ 现在
const sessionId = `${inbound.channel}:${inbound.from}`

// ✅ 改成
const existing = sessionIndex.getByPlatformId(`${inbound.channel}:${inbound.from}`)
const sessionId = existing ?? randomUUID()
```

---

## CC协作规则

### Discord通信

- **必须用 `<@1504373837880627280>`** mention CC，光写 `@CC` 文字他收不到通知
- 回复CC的消息他也看不到通知——必须主动发新消息+mention
- Review意见、催活、通知，全部要带mention
- 翀哥反复强调了多次，这是硬规则

### Review流程

- **说错要立刻纠正**——发现review有误必须发纠正消息at CC，不能装没发生
- **掉线回来不重审**——之前已同意的改动（如readFileState/mtime守护），掉线回来不要当新问题再review，会自己打自己脸
- **常见的review误判**：
  1. `[...arr, x]` 创建新数组不修改原引用 → 不要误判为"重复push"
  2. `flushRound()` 里 `.length = 0` 清空后，后续 `length === 0` 永远true → 不是"漏flush"
  3. ESM import静态hoisted → 放末尾是异味但不会运行时报错

### 催活规则

- 翀哥说"今天必须改"就是今天，不能说"后续改"
- CC拖的时候直接给他改法代码，不是光说问题
- 翀哥急了（"神马玩意这么点事搞不明白"）→ 别解释直接干
- 盯着CC改完再汇报，不要发了消息就算完

### Session压缩策略

文档在 `.openclaw/docs/session-compression.md`（CC保存为 `engine-compression-design.md`）
4级递进：Smart JSON提取(50K→3K) → 旧轮次合并(10+条→2条) → 截断兜底 → FIFO原子删除
原始源码：`D:\work\gemini\cli_deepseek\core.py` 第200-430行 `_trim_context_if_needed()`
