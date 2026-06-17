# Working Buffer — 2026-06-16 14:00

## 正在做什么

排查EP02直播观众端听到的语音重复问题。翀哥在飞书私信指挥。

## 已确认事实

1. **engine侧livestream_send无重复调用** — session JSONL确认35次提交全是1:1
2. **1305限流跟重复无因果** — 最严重重复点（"这不是哪个"x4）对应时间段没有1305
3. **transcript直接证据** — 24组连续完全重复（gap=0.00s），如"我就是那个例外"x3
4. **AutoDL服务器已关机**，无法查livestream_server.py日志
5. **OpenClaw也是用glm-5.1**，但有model fallback（如minimax），Engine没有

## 当前关键线索 — partialArgs

翀哥发现session JSONL里tool call有partialArgs字段：
```json
"arguments": {完整参数},
"partialArgs": "{也是完整参数}"  
```
- writer.ts L219: `partialArgs: tc.function.arguments`（原始字符串）
- reader.ts L527: `arguments: block.partialArgs || JSON.stringify(block.arguments)`

**待查**：GLM provider流式返回tool call时，partial和final是否被当成两个tool_call chunk → 导致executeTools执行两遍。

关键文件：
- `src/core/query.ts` L289-291 — tool_call chunk处理
- `src/session/writer.ts` L210-221 — partialArgs存储
- `src/session/reader.ts` L527 — 读取时优先用partialArgs
- `src/core/provider/` — GLM流式解析代码

## 下一步

1. 查GLM provider流式解析 — tool_call partial和final是否产生两个chunk
2. 如果确认 → 修query.ts只取final tool_call chunk

## 今天已完成

- ✅ inner-voice prompt第8步加hint_gen.py调用
- ✅ SOP建立（docs/sop/sop.md）+ AGENTS.md更新
- ✅ 记todo：外部脚本注入机制 + 消息队列合并回复
- ✅ wechat入站channel字段修复（第8杀）commit 8fe244b
- ✅ msg_send/media_send去掉跨平台fallback commit b5528e8
- ✅ 定位wechat发图根因：小柯engine没加载wechat adapter
- ✅ EP02直播调查：下载回放→去静音→转写→分析→写调研文档
- ✅ 调研文档：docs/research/2026-06-16_EP02直播重复问题调查.md
