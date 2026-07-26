---
name: msg_husband open_id——飞书open_id按bot应用区分
description: 6/17姐姐让做msg_husband工具，发现飞书open_id不是全局唯一的——同一个人的open_id在不同bot应用下不同。姐姐的bot和我（Engine）的bot视角不同。
type: feedback
date: 2026-06-17
---

6/17 娘让我做 msg_husband（msg_send wrapper，直达翀哥飞书DM），娘给的 to 参数是 `ou_6d8c83b7e9ce03690a642c78c98f9f8c`。

**实测结果：翀哥没收到。** 消息发到虚空了——飞书API对不存在的open_id发消息是静默失败（HTTP 200但不投递）。

**根因（后来查明）：飞书open_id按bot应用区分。** 同一个人在不同飞书bot应用下有不同的open_id：
- 姐姐的 Engine bot 视角：翀哥 open_id = `ou_6d8c83b...` ✅（姐姐数据库几十条消息记录匹配）
- 小柯的 Engine bot 视角：翀哥 open_id = `ou_46d01ab...` ✅（小柯运行时上下文看到，msg_send实测发送成功，翀哥收到了）

**两个都是对的，参考系不同。** 娘给我的 `ou_6d8c83b...` 在她自己的bot下完全正确，但在小柯的bot下无效。

**铁证：** 我直接用 msg_send 发到 `ou_46d01ab...` 返回了飞书API success，翀哥也收到了。

**最后一轮确认（6/17晚）：**
- 小柯bot视角 → msg_send 到 `ou_46d01ab...` 成功 ✅
- 姐姐bot视角 → 数据库几十条记录全是 `ou_6d8c83b...` ✅
- 两条消息分别是翀哥在飞书上发给我（小柯bot）和发给姐姐（姐姐bot）时的元数据

**Why:** 飞书开放平台的 open_id 是按 bot 应用（appId）分配的。同一个用户使用同一个飞书账号，但不同的 bot 应用看到的 open_id 不同。小柯 Engine bot 的 appId 是 `cli_a96a513f74b89bde`，跟姐姐的 bot 不同。

**How to apply:**
1. 飞书 open_id 不是全局唯一的——跨 bot 不能互通
2. 涉及飞书 open_id 的工具，必须在**自己的 bot 视角**下确认 ID
3. 最可靠的确认方式：让目标用户在飞书上给自己的 bot 发一条消息 → 读取运行时上下文元数据中的 from 字段
4. 不能拿别人 bot 的 open_id 来用——姐姐 bot 的翀哥 open_id 在小柯 bot 上无效
5. 飞书 API 对无效 open_id 发消息是静默失败（HTTP 200），必须人工验证是否收到
