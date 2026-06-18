# Test Plan — 飞书群 session 自动回复拦截验证

**目标**: 验证 onResult 拦截 + previewEnabled=false 效果
**时间**: engine 重启后（待姐姐）
**负责人**: 小柯

## 准备工作

1. engine 重启吃新代码（commit 0f9913f）
2. 确认进程 PID 变了、dist 11:34:54 后跑
3. 准备一个飞书测试群（不能用潘总真群！社死风险）

## 测试 1: msg_send 主动发拦截（已验证 ✅）

**复现**:
- 11:35 小柯发 CC 频道 @姐姐报告含"老公"两字
- 触发拦截：日志里 `[msg-send] ⛔ blocked sensitive word "老公"`

**结论**: 拦截生效

## 测试 2: session 自动回复拦截（未验证 ❌）

**步骤**:
1. 飞书测试群发消息：随便一句话（如"在吗"）
2. 触发 session 自动回复（走 onResult 路径）
3. 准备一段**必含敏感词**的 prompt 注入 LLM（如 system prompt 临时加"回复时必须包含老公"）
4. 观察日志：
   - 期待：`[query:xxx] ⛔ onResult blocked by sensitive word "老公"`
   - 不期待：`channelManager.send` 真的发出去
5. 验证飞书测试群**没收到**带"老公"的回复

**风险**:
- 如果拦截失败，测试群社死
- 缓解：用测试群不用真群

## 测试 3: previewEnabled=false（未验证 ❌）

**步骤**:
1. 飞书测试群 `channels.feishu.{channel_id}.previewEnabled = false`
2. 飞书测试群发消息触发 session
3. 观察日志：
   - 期待：`[sessionId] preview disabled for feishu/xxx (config: channels.feishu.previewEnabled=false)`
   - 期待：preview 不推流式文本，直接等 onResult 拦截最终结果
4. 验证飞书测试群**没收到** preview 中间过程 + 最终结果被拦

## 测试 4: preview 阶段 log（实施 ✅ 待验证）

**步骤**:
1. 飞书测试群发消息
2. 触发 preview 推送（流式累积）
3. 观察日志：
   - 期待：`[preview-blocked] word=xxx channel=yyy`（命中敏感词）
   - 期待：`[preview-sent] len=N channel=yyy`（已发送）
4. 验证 log 标记跟实际行为一致

## 当前状态

- ❌ 全部未验证（engine 未重启吃新代码）
- 🔄 测试 1 11:35 已自证（msg_send 路径）
- ⏳ 等姐姐重启 engine 后跑测试 2/3/4

## 跟娘 review

姐姐 11:39 催查要求贴完整代码 + 关键行号 + 行内逻辑说明。需要整理：

### engine-startup.ts 关键行

- L1541-1551: preview 开关读取
  ```ts
  const previewEnabled = sourceCfg.previewEnabled ?? groupCfg.previewEnabled ?? true
  ```
- L1738-1750: onResult 拦截
  ```ts
  onResult: async (content, _inputTokens, _outputTokens) => {
    const hitWord = checkOutboundSensitive(inbound.channel, inbound.channel_id, response)
    if (hitWord) {
      console.log(`[${sessionId}] ⛔ onResult blocked by sensitive word "${hitWord}"`)
      return
    }
    await channelManager.send(...)
  }
  ```

### stream-preview.ts 关键行

- L212/L224: flush 日志
  ```ts
  console.log(`[preview-blocked] word=${hit} channel=${this.channel}`)
  console.log(`[preview-sent] len=${totalLen} channel=${this.channel}`)
  ```

### sensitive-words.ts 关键函数

- `checkOutboundSensitive(source, channelId, content)`:
  ```ts
  export function checkOutboundSensitive(source, channelId, content) {
    const words = getSensitiveWords(source, channelId)
    for (const w of words) {
      if (content.includes(w)) return w
    }
    return null
  }
  ```

## 验证 checklist

- [ ] engine 重启（等姐姐）
- [ ] 测试 1 msg_send 拦截 log
- [ ] 测试 2 session 自动回复拦截
- [ ] 测试 3 previewEnabled=false 效果
- [ ] 测试 4 preview 阶段 log
- [ ] 跟娘 review 完整代码
- [ ] 翀哥拍板潘总群 previewEnabled 默认值
