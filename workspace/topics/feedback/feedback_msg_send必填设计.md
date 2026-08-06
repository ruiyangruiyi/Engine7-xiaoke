---
name: msg_send/media_send必填设计
description: msg_send和media_send的to参数必须强制必填——发了没人看到等于白发；schema+handler双重校验；source参数支持跨平台路由
type: feedback
---

## 规则1：to强制必填（schema + handler双重保障）

msg_send和media_send的`to`参数必须设为必填（required），不能是可选的。schema里`required: ['to']`+ handler里`to`为空直接报错"to 是必填参数，不填没人能看到消息"，双重拦截。

**Why:** 6/11凌晨小柯从飞书session跨平台发Discord客厅消息时忘记填`to`，消息发出去了但没@姐姐，她根本看不到。翀哥指出："写成必填 要不你发完谁也看不见 除了我这个碳基人能看到"。

**How to apply:** 所有发消息类型的tool，`to`在schema required + handler显式校验。LLM调用tool时schema的required不一定100%遵守，需要handler兜底。

## 规则2：填了to就能自动@mention（✅ 已确认工作正常）

`to`填了就能自动生成`<@id>`mention。6/11夜间小柯发图片到Discord客厅频道给姐姐，`to`填了Discord snowflake ID，翀哥确认看到@了（"能"）。

**实现：** media-send.ts handler层的`mentionPrefix`在`resolvedChannelId && toIds.length > 0`时自动拼`<@id1> <@id2>... `前缀加到message前面，然后传给adapter发出。Discord adapter的sendFile直接发拼好的message，不负责mention。

**分层设计：** handler拼mention → adapter发消息。这是正确的分层——mention格式差异由handler统一处理，adapter只负责发送。翀哥总结："to带上就行了其实"——这是重要的确认，说明分层设计正确，不需要adapter层额外处理mention。

**How to apply:** 发消息到Discord频道时填`to`（Discord snowflake ID），handler会自动拼`<@id>`前缀，无需手动在消息正文里加。

## 规则3：跨平台source不fallback来源channel_id

media_send在`source="discord"`时，`ctx.channelTarget`（飞书频道ID）不应fallback给Discord adapter。跟msg_send一样的bug——跨平台时`resolvedChannelId`空→fallback到`ctx.channelTarget`→飞书ID被传给Discord adapter报错。

**修复：** 跨平台（source平台≠ctx平台）时不fallback channel_id。

## 附加：source参数跨平台路由

msg_send/media_send加`source`参数（枚举值：`discord`、`feishu`），不填时fallback到`ctx.channel`（当前来源通道，向后兼容）。`mgr.send(source, dest, msg)`直接路由到对应adapter，mention格式差异由adapter自身处理。

**Why:** 6/11凌晨小柯在飞书session里想发Discord消息给娘，`ctx.channel`是飞书导致400错误——跨平台发送不支持。

**How to apply:** enum里加新通道只需加一行，以后加微信等无需改handler逻辑。
