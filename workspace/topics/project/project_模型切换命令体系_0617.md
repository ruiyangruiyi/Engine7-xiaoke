---
name: 模型切换命令体系——/model /vision-model /primary
description: 6/17完成三个模型切换命令的完整设计与实现：/model临时切文本、/vision-model临时切视觉、/primary持久化改默认
type: project
date: 2026-06-17
---

6/17 完成模型切换命令整体设计：

## 三命令体系

| 命令 | 作用 | 时效 |
|------|------|------|
| `/model` | 临时切文本模型 | 立即生效，重启回默认 |
| `/vision-model` | 临时切视觉模型 | 立即生效，重启回默认 |
| `/primary` | 持久化切默认模型 | 写入 config 文件，重启生效 |

## 配套改动

1. **Vision 路由修复** — 有图始终走 vision 模型，`/model` override 不劫持图片消息
2. **文本命令拦截** — `/model` 等命令在 ChannelManager 层拦截，不依赖 LLM 可用
3. **FallbackProvider** — stream error 自动切模型，24h 冷静期，`/model auto` 恢复

## 同日其他改动

1. **msg_husband 工具** — msg_send wrapper，直达翀哥飞书DM。⚠️ 踩坑：飞书open_id按bot应用区分，不能交叉使用。娘给的ou_6d8c83b...是她bot视角的ID，在我小柯bot上无效。已修正为运行时上下文确认的 ou_46d01ab...。
2. **群聊敏感词过滤器(msgGuard)** — 群消息发前扫描敏感词，命中则拦截。⚠️ 踩坑：substring匹配导致"appId"里的"PP"误伤。翀哥纠正：敏感词和白名单都从config读，代码不写死。最终架构：config注入registry.config，tool handler动态读取。
3. **Discord频道白名单** — 翀哥说"先别限制频道了"，暂时空着不启用。

## 状态

全部完成并已提交、重启生效。TestEngine review 通过："可以合，没毛病"。

## 踩坑记录

6/17 翀哥发 `/vision-model zhipu/glm-5v-turbo` 没被拦截 → 正则 `\w+` 不匹配 `-`，已修复为 `[\w-]+`。
