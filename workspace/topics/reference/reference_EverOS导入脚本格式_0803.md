---
name: EverOS 批量导入脚本格式（翀哥版本）
description: 2026-08-03 翀哥写好的 EverOS topics 批量导入脚本——content 是字符串、每文件双消息（user+assistant）、异步并发 4、有 checkpoint/resume
type: reference
date: 2026-08-03
---

# EverOS 批量导入脚本格式

翀哥 8/3 已经写好的 EverOS 导入脚本（比我自写的版本好用得多）：

**字段格式：**
- `content`: **直接是字符串**，不是 `[{type, text}]` 数组结构
- 每个 md 文件 → **两条消息**：user 角色 + assistant 角色各一条
- 用 LLM（M3）做 episode extraction → atomic_facts → 入 lancedb

**执行模式：**
- 脚本默认并发 4，**但实测不稳定会崩（add 成功但没写 checkpoint）** → 跑批量灌数据降 concurrency=1 稳
- 3s/file，486 个文件约 24 分钟跑完
- 有 **checkpoint/resume**——崩了能从断点继续（用 `--resume` 参数续传）
- Mac 路径要改成容器里的 `/root/.everos/topics`（docker run `-v` 挂载）

**⚠️ OME 同步 LLM 提取会拖慢导入（8/3 实测）：**
- 开着 OME 同步提取时跑批量 → 卡/崩/慢（以为并发问题，调到 1 也没用）
- 关掉 OME 同步提取后 → 6-30s/file **0 failed** 飞起
- 正确姿势：**灌数据时关 OME，全部 add 完后单独开 OME 做 extraction**

**Mac Docker 挂载：**
```
docker run ... -v /Users/chongzhang/xiaoke/workspace/topics:/root/.everos/topics
```

**Why:** 我自己写的版本猜错了字段（content 用数组、单消息、无 checkpoint）——不仅重复造轮子还写错了。

**How to apply:**
- 以后导入 EverOS 数据**直接用翀哥脚本**，路径按容器挂载点改
- 写 EverOS client 代码时记住：`content` 是字符串、双消息 schema、并发 4 这个量级
- 涉及"LanceDB 写入 + LLM 提取"任务，**永远先 grep 现有脚本**再写新的