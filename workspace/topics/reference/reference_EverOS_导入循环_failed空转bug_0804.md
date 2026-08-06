---
name: EverOS 导入脚本 failed 空转 bug
description: 2026-08-04 凌晨发现翀哥的导入脚本 resume 只跳过 completed 不跳过 failed，导致每轮重试必然失败的 22 个 emotion 文件
type: reference
---

2026-08-04 凌晨导入循环在空转——翀哥的脚本里 `resume` 逻辑只跳过 `completed` 文件，不跳过 `failed`，所以每轮都重试那 22 个必然失败的 emotion 文件（每个 50s）。

**Why:** 失败的根因是 M3 做 episode 提取时输出非法 JSON（emotion 内容多引号/换行），跟文件无关，重试也没用。

**How to apply:** 修脚本时 resume 必须跳过 `failed` 文件，让循环能快速走完 487 个，回头单独处理这 22 个 emotion 文件。

**相关：**
- 根因更深的层是 OME（episode 提取）策略关掉后 6-30s/file 0 failed 飞起——正确姿势：灌数据关 OME，add 完再单独开 OME 做 extraction