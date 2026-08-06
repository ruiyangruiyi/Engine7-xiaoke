---
name: groupToolDisplay 内部/外部群分控——外部群强制关
description: 2026-08-04 晚发现外发群 toolDisplay 代码——isGroup + channelCfg.group.toolDisplay;翀哥要求外部群(externalChannels)强制关 toolUse/toolResult 防内部信息泄露
type: reference
date: 2026-08-04
---

# groupToolDisplay 内部/外部群分控——外部群强制关

8/4 翀哥要求：外部群（externalChannels 白名单里的飞书群）不显示 tool 信息，避免内部工具调用泄露到外人面前。

## 现状代码（8/4 改前）

```js
groupToolDisplay = isGroup ? channelCfg?.group?.toolDisplay === true : true
```
- 群（任何群）默认 false，DM 默认 true
- 内外群没区分——外部群一旦设 true 就显示

## 翀哥要求改的

翀哥说"外部群关 toolUse/toolResult 防泄露"——核心诉求是**外部群不泄露内部信息**。
reactions（👀✅❌）他明确说保留不动，不算敏感信息。

## 实施路径

判断 channel_id 是否在 externalChannels 列表里，外部群强制 `toolDisplay=false`：
- 加一层 `isExternal = externalChannels.includes(channelId)` 判断
- `groupToolDisplay = isExternal ? false : (isGroup ? channelCfg?.group?.toolDisplay === true : true)`

## 涉及的三个显示

翀哥说的"toolResult"——三个全局开关：
1. **thinking** 显示——已接 `groupToolDisplay` 判断
2. **toolUse** 显示——已接 `groupToolDisplay` 判断
3. **toolResult** 显示——config.toolResult 全局 `enabled: false`，群内不显示具体结果
4. **reactions**（👀✅❌）——全局控制，没内外部区分

## Why

- 外部群有外人/客户/曲教授——内部 toolUse 暴露代码路径和敏感操作
- 内部群和 DM 是翀哥/姐姐自己用，工具信息可读性优先
- reactions 保留是因为它是辅助信号不是工具信息

## How to apply

- 后续加新的群相关显示开关，默认按 `groupToolDisplay` 同款分内外处理
- 改完别忘 Docker build 推 dist，等翀哥/姐姐重启 engine 才生效（@see feedback_Mac_没人帮我重启engine_0803）
- externalChannels 白名单从 config 顶层读（@see feedback_external-chan_白名单从contacts读不稳定_改config_0621）
