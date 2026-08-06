---
name: 外部群自动关闭 groupToolDisplay——不泄露内部信息
description: 2026-08-04 小柯改源码让 externalChannels 列表里的飞书群自动关 toolDisplay/thinking/toolResult，reactions 保留，等翀哥出院后重启生效
type: project
date: 2026-08-04
---

# 外部群自动关闭 groupToolDisplay

8/4 下午翀哥核心诉求——**外部群（externalChannels 白名单里的群）不泄露内部信息**。

## 已做的改动

- `groupToolDisplay = isGroup ? channelCfg?.group?.toolDisplay === true : true` → 加判断 `externalChannels.includes(channel_id)` 时强制 `false`
- 这个变量同时控制三处显示：**thinking / toolUse / toolResult**
- 改动后 Docker build + push 出 7.1.28+ dist，已 push 到翀哥 Mac（@see project_Docker_build链_Mac_esbuild跑不了_0804）
- 8/4 12:14 小文帮小柯重启成功（新 PID 13458）→ 翀哥在飞书测试群 oc_f5d614d176cca078a029c55f99ae2d4b 验证时**工具调用还在显示**——说明代码改动没完全生效，路径里可能还有未受 groupToolDisplay 控制的发送点（待排查）

## Why

- 翀哥的核心诉求是"不泄露内部信息"——外部群用户不该看到我在调试/读文件/调工具的全过程
- 之前需要 channelCfg.group.toolDisplay 配置来关，但翀哥默认 `toolDisplay: true` 不改 config 一直开着
- 加白名单自动判断比让翀哥逐个群改 config 更稳

## How to apply

- reactions（👀✅❌）**保留**——翀哥 8/4 确认这就是他的本意，外部群也想看到表情反馈
- toolResult 全局已经 `enabled: false`，不影响 DM/内部群
- 内部群和 DM 不受影响，只 externalChannels 列表里的群自动关
- @see feedback_toolDisplay不是channel配置是顶层toolUse_0803——channel config 的 toolDisplay 是 group 维度，跟顶层 toolUse.enabled 是两套