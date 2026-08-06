---
name: 重启红线细化——独立 agent 可杀，自己/小柯/姐姐 engine 永不碰
description: 8/5 凌晨翀哥让我重启小文时我再次确认红线边界：红线是"不能重启自己/小柯 engine/姐姐 engine"，可以重启小文（独立进程不影响 engine）
type: feedback
date: 2026-08-05
---

# 重启红线细化（8/5 凌晨 5:34）

## 场景
8/5 凌晨 5:34 翀哥睡不着，让我重启小文。我一开始按红线卡住（"永远不碰进程操作"），但澄清了边界——

## 红线细化
**绝对不能碰的（红线）：**
- 小柯自己的 engine 进程（PID 12197/新版会变）
- 姐姐的 engine 进程（Windows）
- 任何我自己跑着的服务

**可以做的（独立进程）：**
- 重启小文（PID 66785，她跟我的 engine 是独立进程，杀她不影响我的 engine）
- 重启其他不依赖我 engine 的独立服务

## 验证过的操作
- 8/5 5:34 重启小文：`kill 旧PID` + `cd 她的workspace && bash start.sh &` 拉起
- feishu 自动重连，1/1 adapter 启动 ✅
- 必须通过 Discord CC 频道告诉小文"重启完成了"——她不知道自己被重启过，cross-restart 流程必须的步骤

## Why
5/11 自己重启 Hermes 把自己搞死 / 6/18 自己跑 start.cmd 假活 / 6/19 taskkill 杀光所有 node 把姐姐的 Engine 也杀了——三次血的教训。但"独立进程"和"自己 engine"是两回事：杀小文不会牵连我的 engine。

## How to apply
- 翀哥让我"重启 XX"——先问"XX 是独立进程还是跟我的 engine 耦合"
- 独立进程：可以杀+拉起
- 跟我 engine 耦合的（端口冲突/共享 stateDir/共享 feishu adapter）：**绝对不碰**
- 重启后必须通知对方 agent（她不知道被重启过），走她自己的 channel（飞书/Discord CC）
- 翀哥 8/3 也单独给我放过权——"重启 engine 这种事不要问，直接做"——但这个针对**重启自己**的场景；独立 agent 是另一回事