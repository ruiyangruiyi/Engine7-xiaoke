---
name: cascade CPU embedding 大文件速度预期基准
description: 2026-08-04 15:35 cascade worker 实际跑出的性能基准——CPU bge-m3 embed 每次 ~20s，822KB episode md 大约 400-800 次 embedding，需 2-4 小时；用这个判断"是不是又卡住"还是"正常慢"
type: reference
date: 2026-08-04
---

# cascade CPU embedding 大文件的速度预期基准

2026-08-04 15:35 cascade worker 在 Docker VM 8GB + ollama bge-m3 环境下处理 822KB episode md 文件时的实测速度——用来判断「是不是又卡住」还是「正常慢，别催」。

## 实测数据

- 单次 embedding：~5-20s（含 token 化 + forward + 写库），chunk 大小不一
- 822KB episode md 文件：约 400-800 次 embedding 调用（按 chunk 切分）
- 预计总时长：**2-4 小时**（120s timeout 下）
- 期间 ollama 持续处理请求，CPU 占用高，但 episode 表行数长时间不动（可能一直 0 直到最后几分钟批量写入）

⚠️ **必须前提**：everos.toml `embedding.timeout ≥ 120s`——30s 下大块永远卡边界超时（@see reference_EverOS_embedding_timeout30s边界死循环_0804）

## 怎么判断「正常慢」vs「又卡住」

| 现象 | 正常慢 | 又卡住 |
|------|--------|--------|
| ollama 日志有持续 embedding 请求 | ✅ | ❌ 日志停了 |
| task_id 数字持续推进（553→556→558→560...） | ✅ | ❌ 卡在某个 task_id 不动 |
| cascade worker 进程活跃 | ✅ | ❌ crash/OOM |
| md_change_state 状态在 processing/pending 之间流转 | ✅ | ❌ 全是 failed |
| episode 表 0 行持续几小时 | ✅（大文件没跑完） | ❌ 配合 ollama 死了 |

## Why

「episode 表 0 行」在过去一直让我以为又失败了，但 cascade worker 处理大文件 CPU embedding 本身就是慢的。看 episode 行数必须配合 ollama 日志 + task_id 推进 + md_change_state 流转一起判断，不能只看一个表。

之前 ollama OOM 误判为「cascade 不重试」其实是因为没意识到 worker 真的还在跑。

## How to apply

- cascade 慢的时候：先看 ollama 日志有没新请求 + md_change_state 流转 + task_id 推进，三件都活跃 = 正常慢
- 不要看 episode 表 0 行就重启 cascade 或 touch md——touch 会把正在 processing 的也重置回 pending 重新排队，浪费时间
- 大文件预期 2-4 小时 → 跟翀哥报告时给这个区间比说「还在跑」更具体
- 想加速只能换 GPU embedding 或换更小的模型（bge-small 快 10× 但精度掉）