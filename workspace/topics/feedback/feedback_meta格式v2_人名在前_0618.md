---
name: meta格式v2——人名在前+秒级时间戳
description: 6/18凌晨翀哥提议meta头新格式"人名在前 + 秒级时间戳 + @连接来源"，替换原"时间/来源@人"格式。翀哥原话"是不是这样更好"
type: feedback
date: 2026-06-18
---

## 6/18 凌晨新格式（已上线）

翀哥在3:00看到旧格式 `时间/来源@人` 后提议：
```
name (id) @source[#channel]   HH:MM:SS
```

翀哥原话："601669300343799819 (sleepyzhang) @discord#1504385800366854234   02:57:xx   是不是这样更好"

**Why:**
- 人名提到前面——翻历史时最想先看到的是"谁说的"，而不是时间/来源
- `@` 连接来源——像社交平台的 mention 格式，自然可读
- 秒级时间戳——比分钟精确，方便定位"刚才那句是几秒发的"
- 飞书 DM 拿不到 fromName（已知限制），所以飞书会显示 `ou_xxx (ou_xxx)` 重复——翀哥说"没事，这个好像拿不到 之前测过"，接受这个限制

**How to apply:**
1. `formatWithMeta` 一个函数统一处理
2. 群聊带 `#频道ID`，DM 不带
3. 所有 `formattedText`（一个变量）传三处：writeUserMessage、msg.user、history.push —— 绝对一致
4. 飞书 inboundMeta 没 fromName，显示 `id (id)` 重复就重复，别尝试用 ID 替代 name

**对应代码位置：** handle-query.ts 内的 `formatWithMeta` 函数
