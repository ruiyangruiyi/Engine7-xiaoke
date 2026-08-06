---
name: meta格式v4——加[meta:前缀+contacts.md哈希表反查名字
description: 6/18 08:44姐姐转达翀哥定稿：v3基础上加[meta:前缀做视觉分隔+启动读contacts.md建dict反查名字
type: feedback
date: 2026-06-18
---

## 6/18 09:01 实测成功

翀哥08:52重启后，从Discord发的消息meta头正确显示：
```
[meta: 翀哥 (601669300343799819) @discord 09:01:39]
```
contacts.md 哈希表反查 Discord ID `601669300343799819 → 翀哥` 命中。微信/飞书的反查也确认OK（详见feedback_esm_bundle_require_fs踩坑_0618.md踩坑修复）。

## 6/18 08:44 姐姐转达翀哥定稿

### 改动1：加回 `[meta:` 前缀
v3格式（`name (id) @source[#channel]   HH:MM:SS`）没前缀，元数据和正文黏在一起。加前缀做视觉分隔。

### 改动2：contacts.md ID→名字反查（启动时建哈希表）
飞书/微信 API 不返回名字只返回 ID。**启动时读 contacts.md 建 dict**，每条消息 O(1) 查表拿名字，**不走文件 IO**。

启动时一次读：
```python
{
  ou_6d8c83b... → 翀哥
  o9cq80_xQec... → 翀哥
  ou_46d01ab... → 晓梅
  1503660074... → 张小柯
  6016693003... → sleepyzhang
}
```

formatWithMeta → `dict.get(senderId) ?? senderId`

### 最终格式
```
[meta: 翀哥 (o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat)]
```

## 与 v3 的关系
- v3 是 6/18 03:01 翀哥拍板的人名在前+秒级时间戳格式
- v4 = v3 + `[meta:` 前缀 + 联系人哈希表（解决微信adapter拿不到名字+飞书fromName缺失）

## Why
1. v3 格式没前缀，元数据跟正文黏一起，需要视觉分隔
2. 微信adapter L791 fromName=senderId 是历史遗留——以前meta只显示ID所以没暴露
3. 飞书fromName也拿不到（API硬性限制）
4. contacts.md已经在workspace里维护，启动读一次比每条消息文件IO快得多

## How to apply
1. formatWithMeta 头部加 `[meta: ` 前缀
2. engine启动时读contacts.md建dict（key=各平台ID，value=名字）
3. formatWithMeta 内部用dict.get(senderId)代替直接用fromName
4. contacts.md要维护完整——三平台ID都要有（飞书/微信/Discord）
5. 改完三通道实测（跟v3教训一脉相承）
