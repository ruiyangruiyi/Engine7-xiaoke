---
name: 小忆hint根因（6/18凌晨定位）
description: 6/18凌晨05:48定位：session_history.py没过滤系统注入的user消息(heartbeat/inner-voice/微信巡检)，误判翀哥活跃→hint概率锁50%→大多不命中。跟heartbeat问题是同一根因。
type: project
date: 2026-06-18
---

## 现象
- 翀哥3:49看context debug确认没有hint
- xiaoyi.log也没输出hint
- 4:41有过一次hint=YES，但注入的念头里没看到💡

## 排查过程（05:33-05:48，翀哥睡着时查的）
1. ✅ cron在跑（xiaoyi.log最后更新05:43），hint_gen.py执行了
2. ✅ 但 `hint=no prob=50%` 一直不变
3. ✅ 姐姐context-debug里有 `[inner-voice]` 念头注入（[430]-[477]），念头注入链路正常
4. ✅ 04:41有过hint=YES（log里能查到），但注入时是另一条hint=no的念头覆盖了

## 根因
`get_silence_minutes` → `session_history.py` 读"最后用户消息"时，**没过滤系统注入的user消息**：
- inner-voice注入的念头（走user通道）
- 微信巡检cron注入的汇报（走user通道）
- heartbeat心跳注入（user通道）

所以即使翀哥3:55就睡了，`session_history.py` 看到的"最后用户消息"是30分钟前的inner-voice注入（或微信巡检注入），`mins` 永远很小（<60）→ hint概率锁在50% → 大多不命中。

## 这是跟heartbeat同一个根因
翀哥3:54说的第三个紧急问题："heartbeat被inner-voice注入消息骗过"——heartbeat检测"是否有user活动"时也把inner-voice注入当成真实用户活动跳过。

**两者都是系统注入的user消息没被区分出来。**

## 修复方向（明天动手）
1. session_history.py 读JSONL时过滤系统注入消息——可加标记识别（如messageId前缀/source=inner-voice或cron）
2. heartbeat同样需要过滤——或者改用"真实用户消息时间戳"判断活跃度
3. 一个统一方案：在系统注入user消息时加 `system: true` 标记或source字段，所有读取活跃度的脚本统一过滤

**Why:** 之前session_history.py设计只考虑了"心跳/HEARTBEAT_OK要过滤"，没考虑"内心独白/微信巡检也是user通道注入"，导致过滤列表不全。

**How to apply:** 以后涉及"用户活跃度判断"的代码（session_history.py/heartbeat）必须把"系统注入"和"真实用户消息"区分开，**不能只看JSONL最后一条消息的role是user**。

## 6/18 09:01 翀哥确认可动手
> "hint根因查完了——你说的heartbeat被inner-voice骗，跟hint不出来是同一个bug。session_history.py没过滤系统注入的user消息，把inner-voice和微信巡检当成你的真实消息了，所以hint概率永远卡在50%。你醒了细聊，修法我也想好了。先喝口水。"
> "开始弄这个 小柯 就是看看怎么过滤"

## 6/18 09:09 修完了

翀哥确认根因后我开始动手。核查发现：
- `[inner-voice]` 和 `【定时心跳】` 在 `INJECTED_CONTENT_PATTERNS` 里**已经存在**（6/15 加的）
- **缺的是 `[微信巡检]`**——姐姐 session 有 29 条 `[微信巡检] [SILENT]` 以 user role 注入 JSONL，没被过滤掉

修了两个 `session_history.py`：
1. 小柯的：`/Users/chongzhang/xiaoke//scripts/session_history.py`
2. 姐姐的：`/Users/chongzhang/xiaoke/workspace/scripts/session_history.py`

两个都补了：
- `[微信巡检]` pattern
- `[pre-compaction]` pattern（顺手加，防未来 PreCompact hook 注入漏掉）

**验证通过：**
- 小柯：`last_user_msg` 返回翀哥 09:01 的真实消息，正确
- 姐姐：`last_user_msg` 返回翀哥 09:08 的飞书消息（之前一直返回最近一条 `[微信巡检] [SILENT]`）

Python 脚本实时读，下个 cron 触发就生效，不需要 rebuild engine。

## 验证数据
- 05:33 session_history.py返回的最后"用户消息"时间戳是05:33（微信巡检cron注入）——距翀哥3:55真实消息仅2分钟
- 翀哥实际睡了2小时，但脚本认为2分钟前还在活动