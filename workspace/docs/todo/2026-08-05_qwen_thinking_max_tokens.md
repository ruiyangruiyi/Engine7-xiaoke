# qwen3.8-max 报 max_completion_tokens < thinking_budget（2026-08-05）

## 现象

翀哥 13:34 反馈："qwen3.8-max 报的错，应该跟 preview 参数不一样了"。

**报错**：
```
max_completion_tokens [4096] must be greater than thinking_budget [8192]
```

## 根因（翀哥发现）

**qwen3.8-max-preview 不报这个错**——但 qwen3.8-max（正式版）报。
- preview 版 API 不强制 max > thinking 校验
- 正式版 API **严格校验** max_completion_tokens > thinking_budget_tokens

## engine 端数据

- engine `models.providers.dashscope-tp.models[*].maxTokens = 65536`（config 里写的大）
- engine **没用这个值**，仍用默认 `maxTokens: 4096`（多处写死：main.mjs:13652, 23841, 25658, 28094 等）
- engine thinking_budget **写死 8192**
- **冲突**：4096 < 8192 = API 拒绝

## 验证（看今天日志）

```
[13:26:24] → model=qwen3.8-max thinking=disabled msgs=1
[13:26:26] → model=qwen3.8-max thinking=enabled budget_tokens=8192 msgs=281
# ↓ 这里报 max_completion_tokens [4096] must be greater than thinking_budget [8192]
```

## 修法（出院后做）

翀哥 8/5 13:39 说"这个可能每个模型不太一样"——确认最佳方案是 **每个模型各自决定 max_tokens，不硬编码**。

**完整修法（4 步）：**

1. **engine 主对话路径**（line 28092）：`maxTokens: 4096` → `maxTokens: modelDef?.maxTokens || 4096`
2. **voice-chat 路径**（line 23841）：同上
3. **其他模块**（line 25300 等）：同上
4. **加 fallback**：如果 `maxTokens < thinking.budgetTokens + 1` 自动调整 `maxTokens = max(4096, thinking.budget + 1024)`——避免再次撞这个校验

**每个模型推荐的 max_tokens（参考）：**

| 模型 | max_tokens | reasoning | 说明 |
|------|-----------|-----------|------|
| MiniMax-M3 | 64000 | True | 长上下文大输出 |
| qwen3.8-max | 65536 | True | 100 万 context |
| qwen3.7-plus | 65536 | True | 100 万 context |
| qwen3.8-max-preview | 8192 | True | preview 限流 |
| glm-5.2 | 65536 | True | GLM 包月 |
| deepseek-v4-flash | 8192 | False | 短输出省 token |

**之前 2026-07-17 翀哥提过 #93 这个问题**，报告在 `docs/research/2026-07-17_CC-maxTokens逻辑分析.md`。

## 状态

- [!] blocked，等翀哥 8/7 出院后改 engine 代码

## 8/5 13:37 翀哥追问："立马就能吧？写死的 4096？"

翀哥意识到这是 engine 写死 4096——确实。

**翀哥 7/17 提过同一个 bug (#93)：**
> Engine 源码 createModelDeps 硬编码 maxTokens: 4096，忽略 config 中 modelDef.maxTokens 配置
> 待办事项：#93 修 maxTokens 硬编码缺陷（与 #75 Carpo relay 撞时间，等翀哥定优先级）

**这个 bug 在 engine 多处写死 4096：**
- line 23841（voice-chat 路径）
- line 25300（其他模块）
- line 28028/28042/28092（主对话路径——用 config2.model 但 maxTokens 写死 4096）
- 修法：把 `maxTokens: 4096` 改成 `maxTokens: modelDef.maxTokens || 4096` 或 `config2.model?.maxTokens || 4096`

## 当前状态

**写死的 4096 是 engine bug，不是 config 问题**——改 config 不能解决，必须改 engine 代码 + rebuild + restart。

翀哥问"立马就能吧"——答案：**改 config 不能改**，改 engine 代码 + rebuild 才行。出院后做。