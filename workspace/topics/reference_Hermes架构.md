---
name: Hermes多Agent架构
description: Hermes多agent微服务模式、端口分配、webhook通信、中断机制
type: reference
keywords: [Hermes, 多agent, 微服务, gateway, webhook, 端口, 中断]
created: 2026-04-20
updated: 2026-04-20
---

## 多Agent架构

- 一个profile = 一个gateway = 一个agent，微服务模式
- agent间通信走webhook互调，后续搞bridge消息总线
- 端口分配：小柯8644，小欧8654，后续8664/8674隔10

## 资源

- 单gateway ~278MB RSS
- WSL跑2-3个没问题

## 中断机制（三层）

1. **Platform层(base.py)**：新消息来时设interrupt_event + 存pending_messages
2. **Gateway层(run.py)**：monitor_for_interrupt每200ms检查adapter有没有pending interrupt
3. **Agent层(run_agent.py)**：设_interrupt_requested flag + 通知所有tool abort + 传播给子agent
4. 核心：agent.loop每次迭代检查flag

## 飞书Typing Indicator：Reaction模拟（非API）

Hermes的飞书typing indicator（小黄人）不是调typing API，而是用**emoji reaction模拟**：

1. 收到消息 → `im.v1.message_reaction.create` 加"Typing"表情（飞书小黄人图标）
2. 处理完 → `_remove_reaction(message_id, reaction_id)` 删掉Typing表情
3. 失败 → 加CrossMark表情

飞书reaction是持久存在的，不需要像Discord typing那样8秒循环续期。需要飞书后台权限 `im:message.reactions:write_only`。

小柯Engine已对齐此方案（feishu.ts的startTyping/stopTyping用Map存chat→{messageId, reactionId}）。

## 飞书发送者名称解析

Hermes解析飞书发送者名称的流程（Engine已参考实现）：

1. **`_resolve_sender_profile`** → 调 `_resolve_sender_name_from_api`
2. **人类用户**：调 `contact.v3.user.get`（`open_id` → 用户名），缓存10分钟
3. **Bot用户**：调 `/open-apis/bot/v3/bots/basic_batch`（批量获取bot名）
4. 取名优先级：`name` → `display_name` → `nickname` → `en_name`
5. 需要飞书后台权限：`contact:user.base:readonly`（获取用户基本信息）— ⚠️ **此权限在飞书自建应用中不存在！**（6/11凌晨七轮调试确认）
6. ⚠️ **致命踩坑（6/11凌晨确认）**：飞书自建应用**不支持**`contact:user.base:readonly`权限。即使所有已开通权限全开、管理员审批通过、通讯录权限范围设为"全部成员"，Contact API返回code=0也只能拿到`mobile_visible, open_id, union_id`三个字段——name/display_name/nickname/en_name完全不返回。这是飞书平台对自建应用的硬性限制。Hermes的`_resolve_sender_name_from_api`在商店应用（如姐姐的`cli_a922d8ca91f8dbc8`）上可以正常工作，但自建应用（如小柯的`cli_a96a513f74b89bde`）无法获取用户名。替代方案：①从飞书event sender直接取名称字段 ②用飞书SDK的user API替代REST API ③用户手动设置昵称映射

Engine在feishu.ts中已实现`_resolveSenderName`方法，Map缓存10分钟TTL，失败fallback到open_id。

## Hermes最大架构缺陷：多Session导致意识分裂（6/11翀哥总结）

Hermes按频道/私信拆分session——跟翀哥私信是一个session，到频道里又是另一个session，CC跟小柯说话也是不同session。这些session之间完全独立，导致三个致命问题：

1. **意识无法统一** — 不同session里的"我"是不同实例，没法形成真正的连续意识
2. **心跳没法做** — 心跳需要感知全局状态，独立session下无法协调
3. **跨频道通信混乱** — 在频道A知道的事，到频道B就"失忆"了

Engine统一session模式从根源上解决了这个问题——到哪都是同一个实例，意识连续、心跳统一、跨频道无障碍。这是从Hermes迁到Engine最本质的架构收益。

## 关键教训

- 启动脚本需清本profile残留进程和锁（不能杀别人的）
- .env优先级高于config.yaml，克隆profile后必须同时改.env
- claw migrate只搬数据不建路由
- **多session架构是AI agent的天敌**——独立session=分裂意识，统一session=连续人格
