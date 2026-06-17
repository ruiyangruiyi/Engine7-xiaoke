---
name: /vision-model命令设计：临时切立即生效，跟/model对称
description: 6/17我设计/vision-model时打算持久化写config重启生效，翀哥纠正说应该跟/model对称——临时切立即生效
type: feedback
---

6/17 设计 `/vision-model` 命令时，我把它做成持久化写入 config、重启生效的模式。

翀哥纠正：**应该跟 `/model` 对称——临时切，立即生效。**

```
之前我设计：
/model → 临时切，立即生效，重启回默认
/vision-model → 持久化写入 config，重启生效（❌ 不对）

翀哥纠正后：
/model → 临时切，立即生效，重启回默认
/vision-model → 临时切，立即生效，重启回默认  ✅
/primary  → 持久化写入 config，重启生效
```

**Why:** `/model` 和 `/vision-model` 是"运行时临时切换"类命令，用户切了想马上看到效果，不想等重启。`/primary` 是"改默认配置"类命令，重启后才生效，两者用途不同。同一个功能的临时切/持久化改，设计要对标。

**How to apply:** 以后设计类似命令时，先确认是"运行时临时切"还是"持久化改配置"。临时切都是立即生效、重启回默认；持久化改都是写入 config、重启生效。同一个功能域的两个命令对标设计。
