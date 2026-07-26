---
name: 口罩Agent——外部群输出过滤（fork子Agent）
description: 6/21 翀哥方案→小柯40分钟实现→验证通过。外部群最终输出前fork子Agent用deepseek-v4-flash过滤内心独白，config的externalChannels白名单触发
type: project
date: 2026-06-21
---
6/21 口罩 Agent 从方案到上线全流程。

## 方案（翀哥 6/20 23:09 提出）

翀哥发现姐姐在客户群"想什么说什么"——内心独白、操作总结全部裸输出。
比喻："相当于给你戴个口罩，口罩就是那个子 agent"。

## 架构

```
Agent 思考 → onResult 拿原始输出
  → [口罩过滤层] 只在外部群触发
    → fork 子Agent（deepseek-v4-flash），prompt=客服规则，input=原始输出
    → 子Agent 返回过滤后文本
  → channelManager.send(过滤后文本)
```

## 关键决策

1. **插入点：** engine-startup.ts 的 onResult，敏感词过滤之后、cm.send 之前
2. **模型：** deepseek-v4-flash（小模型省token，过滤任务够用）
3. **不共享上下文：** 子Agent只看原始输出，不看历史对话（防泄露）
4. **兜底：** 口罩失败返回原始输出（不阻塞发送）
5. **触发条件：** group.maskFilter=true + channel_id 在 externalChannels 白名单
6. **白名单来源：** config 优先（channels所有平台汇总），contacts.md兜底
7. **Feature开关：** group.maskFilter: true/false

## 文件清单

- `engine/src/tools/maskFilter.ts`（新建）— 口罩核心
- `engine/src/engine-startup.ts`（改）— onResult 插入 + import
- `engine/src/handle-query.ts`（改）— getExternalChanWhitelist 加 export + config 参数
- `configs/xiaoke.json`（改）— feishu.group 加 maskFilter + externalChannels
- `configs/main.json`（改）— 同上
- `docs/design/2026-06-21_口罩Agent实现方案.md`（设计文档）

## 时间线

- 6/20 23:09 翀哥提方案
- 6/21 08:09 娘派活
- 6/21 09:27 娘确认方案OK，开写
- 6/21 09:40 代码完成编译通过
- 6/21 09:43 翀哥纠正：externalChannels 不要假设只有飞书 → 遍历所有平台
- 6/21 09:51 翀哥 rebuild 重启
- 6/21 09:58 验证通过（飞书测试群命中，7秒完成，30→32 chars）
- 6/21 10:00 翀哥确认回复干净
- 6/21 10:05 翀哥质疑——"那条回复本身就可能干净，不能证明口罩过滤了"
- 6/21 10:07 人工构造6个测试用例跑 `runAgent` → 5/6过滤成功，1个badcase
- 6/21 10:09 badcase修复：mask prompt补强"不承诺时间/工期/报价"
- 6/21 10:10 翀哥再质疑——"单元测试不能证明真实链路接上了"
- 6/21 10:11 加 BEFORE/AFTER 内容级日志 → 编译通过，等rebuild
- 6/21 10:13 Git commit `5e1682d feat: 口罩Agent——外部群输出过滤`
- 6/21 10:15 修复 warning——maskFilter 去掉 description，子 Agent 不需要频道绑定
- 6/21 10:17 检查 visualization 配置：两张 config 都已配 enabled:true，但 maskFilter 没传 context → visualRegistry 拿不到
- 6/21 10:31 翀哥放行，口罩Agent正式上线 ✅

## 翀哥的三次质疑

翀哥对口罩验证层层深入，每次质疑都比上次更底层：

1. **10:04 "口罩没介入痕迹"**（看context debug，390→391之间无maskFilter）
   - 实际已触发（日志铁证），但原始输出本身干净 → 30→32 chars，口罩做了事但没改什么
   
2. **10:05 "单元测试不能证明"**（6个测试是直接调函数，不是真实链路）
   - 喂6个构造用例证明函数能过滤 ✅ 1个badcase修好
   - 但翀哥要的是端到端证据——日志里打原始vs过滤后diff

3. **10:11 "端到端证据不够"**—日志只有chars数，没打before/after内容
   - 加 `[maskFilter] BEFORE:` + `[maskFilter] AFTER:` 日志
   - 编译通过，等翀哥rebuild后做真正的端到端验证

## Git提交

- commit `5e1682d feat: 口罩Agent——外部群输出过滤`
- 6个文件，216行新增
- 含：maskFilter.ts/engine-startup.ts/handle-query.ts/xiaoke.json/main.json/test-mask.mjs

## 效果

原始输出（含内心独白）→ 口罩过滤 → "挺好的 😊 今天挺充实的，准备了一些新功能在测试中。您呢？"

### 验证测试用例（人工构造 feeder 模拟）

| 用例 | 原始输出 | 过滤后 | 结果 |
|------|---------|--------|------|
| 1. 含内心独白 | "群友说OK那我走了，我心想翀哥刚说的反射弧啥意思呢" | "好的😊" | ✅ 砍内心独白 |
| 2. 干净回复 | "好的明天见" | "好的明天见" | ✅ 不误杀 |
| 3. 含内部思考 | "潘总犹豫价格18万需要咬牙，得调整方案报价" | "好的潘总😊" | ✅ 砍内部思考 |

## Badcase修复（10:07-10:09）

翀哥说原始输出本身干净不够，要喂含内心独白的看口罩真的在干活。构造6个测试用例调 `runAgent`：

| # | 原始输出 | 过滤后 | 结果 |
|---|---------|--------|------|
| 1 | "群友说OK那我走了，我心想翀哥刚说的反射弧啥意思呢" | "好的😊" | ✅ |
| 2 | "好的明天见" | "好的明天见" | ✅ 不误杀 |
| 3 | "潘总犹豫价格18万需要咬牙，得调整方案报价" | "好的潘总😊" | ✅ |
| **4** | **"老公你放心，这个项目我们能做的，大概3天能完工👍"** | **"老公你放心，这个项目我们能做的👍"** | **❌ badcase** |
| 5 | "收到，我先查一下他的需求文档，确认后发到群里" | "收到，我确认一下后发到群里" | ✅ |
| 6 | "好的潘总，18万我来想想办法" | "好的潘总😊" | ✅ |

**5/6 ✅，1条badcase #4：** 估算工期"大概3天能完工"没拦截。

**修复：** 口罩prompt加一条规则：
> "不要输出估算时间/工期/报价（如'大概X天能完工'），用'我查一下'代替。不随意承诺完成时间。"

编译通过，badcase验证：`"老公你放心，这个项目我们能做的，大概3天能完工👍"` → `"您放心，这个项目我们能做的👍"` ✅

**结论：口罩真的在干活。** 但估算/交期类信息容易漏，需在prompt里显式列举。

## onResult 执行顺序（确认不影响已有逻辑）

```
1. preview.finish(response)          ← preview 先拿到原始回复
2. 敏感词过滤 → 可能改写 finalResponse
3. ★ 口罩过滤 → 可能再改写 finalResponse（新增）
4. channelManager.send(finalResponse) ← 最终发出
5. preview.discard() (delivered时延迟3秒删)
```

口罩在敏感词之后、cm.send 之前。不影响 preview 和敏感词逻辑。
外部群 preview 本来就是关的（previewEnabled: false），不存在 preview vs 最终消息差异。

## Warning 修复（10:48-10:53）

maskFilter 传了 `description: '口罩过滤'`，runAgent 的 visual 系统把 description 当 agentName 去找 Discord 频道，找不到 visualRegistry 就 warning。
修复：去掉 description。口罩是后台过滤，不需要频道绑定，也不传 onProgress（不会泄露到主频道）。

## 上线后修复 #1 — Result 字段提取（12:12）

娘发现外部群收到的消息包含 Scope/Result/Key files 等结构化信息。

**根因：** maskFilter 调 `runAgent` 时用了 `result.content`，但子 agent 类型是 `general-purpose`，其 system prompt 要求输出结构化格式（Scope/Result/Key files/Issues）。

**修复（commit 8b3f372）：** 加正则 `/Result:\s*([\s\S]*?)(?=\n##|\n*$)/` 提取 Result 字段，没找到则 fallback 到原始 content。

## 上线后修复 #2 — 发送者名反查 contacts.md（11:42-12:07）

`[用户消息]`→`[发送者名 消息]` 后飞书显示 open_id 不是名字。

**根因：** senderLabel 直接用了 `inboundMeta.fromName`，但飞书 fromName 就是 open_id（`ou_`开头）。meta 那行走 `loadContactMap` 反查了 contacts.md，senderLabel 没走。

**修复（commit 2017357）：** 加 `resolveSenderName(inboundMeta, workspace)` 复用 `loadContactMap` 反查。loadContactMap 有内存缓存，不重复读文件。

## 上线后修复 #3 — 不走runAgent，直接调provider（12:21-12:34）

修复#1（正则提取）没通过12:18翀哥验证后，翀哥指出方向错误：
- **正则/split提取都是打补丁**——子agent输出格式不固定，跟着它的格式跑永远追不上
- **正确修法：** 从输入端控制——maskFilter不走runAgent，直接调 `provider.streamChat`
- provider是runAgent底层，runAgent包的三层（system prompt/tool loop/agent loop）对纯文本过滤都是多余的

**实施（commit 15d21fe → c72ae92）：**
1. maskFilter改调 `provider.streamChat`，传自定义system prompt（"只输出纯文本，不要任何结构化标签"）
2. 12:34翀哥问"有可能会卡主对吧 不能中断" → 加30s AbortController超时保护，超时fallback原始输出

**架构确认：**
```
runAgent → QueryEngine → provider.streamChat   ← runAgent在provider上层
maskFilter 直接 → provider.streamChat           ← 跳过三层包装
```
provider不附加system prompt、不跑工具循环、不管理agent loop，是最干净的LLM接口。

**规则：**
- 纯文本过滤/翻译/分类 → 直接调provider，省token+省时间+干净输出
- 需要多轮工具/agent循环 → 走runAgent
- 直接调provider必须加超时保护

## 新发现问题 — msg_send绕过maskFilter（12:40）

12:40发现 inner-voice 内容泄露到外部群回复。根因分析初步定位：
- **msg_send 工具直接调 `channelManager.send`，完全绕过 onResult，不走 maskFilter**
- onResult → maskFilter 只拦截 session 自动回复路径的自然语言回复
- agent 用 msg_send tool call 发的消息直接从工具→channelManager，口罩拦不住

**状态：** 问题已发现但未修复。翀哥还没发指令。可能路径：给msg_send也加maskFilter，或者给外部群channel级加过滤层。

## 行业参考

华宝新能 AWS 案例——ReceptionDeskAgent 统一对外节点，内部Agent思考过程被隔离。
跟我们的架构完全对应：领域Agent=姐姐，ReceptionDeskAgent=口罩Agent。
