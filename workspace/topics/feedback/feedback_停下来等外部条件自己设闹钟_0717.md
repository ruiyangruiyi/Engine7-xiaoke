# feedback: 停下来等外部条件时自己设闹钟

> 2026-07-17 翀哥反馈

## 问题
agent 等"外部条件"（服务重启/SSH恢复/文件出现）时停了就不会再检查。
凌晨实例：等 vLLM 重启，SSH 风控断了，直接停了，翀哥不得不手动叫我起来。

## 翀哥否决的方案
- **nudge**：依赖 SESSION-STATE 标 in_progress，但我经常不标，所以 nudge 没发挥作用
- **Stop hook 检测**：太重了，还得检查 in_progress，同样的问题

## 翀哥要求
"你还是自己想一想你怎么去 notification 自己吧"

## 我的方案
停下来等外部条件时，自己用 `cron_create` 设定时检查：
- SSH 断了等恢复 → cron 5分钟后检查
- vLLM 重启等加载 → cron 2分钟后 curl 测
- 条件满足 → 干活 + 删 cron
- 条件不满足 → cron 再触发，我再设一个

**本质：停下来之前先想"我在等什么"，然后自己设闹钟。不依赖任何外部状态标记。**

## 为什么不用 run_background
run_background 有 notification，但很多时候没法用：
- SSH 连不上的时候根本没法 run
- 有些操作不是"跑命令"而是"去检查状态"
