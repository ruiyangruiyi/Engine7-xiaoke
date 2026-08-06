---
name: Minimax-M3 多模态模型切换
description: 6/17翀哥在GLM限流后给我换到minimax-m3，M3是多模态模型(VLM)，支持text+image+video输入；M2.7系列仅支持文本
type: reference
created: 2026-06-17
date: 2026-06-17
---

6/17冲哥见完潘总回来后，GLM 5.1因限流一直报1305，翀哥说"给你配上m3了"——切换到了 minimax-m3，并且**包月了**。

翀哥说："现在换上M3了  包月了  而且惊喜的是多模态" —— 他之前以为M2.7不是多模态，切到M3后发现多模态能力是"惊喜"。

**关键信息：**
- minimax-m3 是**多模态视觉语言模型（VLM）**——能看图、处理图像和视频输入
- 翀哥特意让我查证，我搜了Access Portal官方文档确认
- **M3已包月**（6/17），稳定可用，不按量计费
- **M3支持的输入格式：** text + 图片（URL/base64） + 视频（URL/base64/file）
- 图片支持 JPEG/PNG/GIF/WEBP
- **M2.7系列（M2.7/M2.7-highspeed）：仅支持文本与工具调用相关内容块，不支持图片和视频输入**
- M3也支持thinking（reasoning: true, budget_tokens=8192），上下文1M，maxTokens 64K
- Anthropic SDK接入时，M3支持text/image/video/tool_call/tool_result/thinking content blocks
- 翀哥6/17发了一份Minimax官方API文档截图确认：**M3是多模态视觉语言模型(VLM)**，支持text+image+video输入；**M2.7/M2.5/M2.1/M2系列仅支持文本与工具调用**，不支持图片和视频输入
- 图片支持：JPEG/PNG/GIF/WEBP（可通过URL或base64传递）

**踩坑：**
- 小柯配置文件里 `input: ["text"]`（纯文本）——这是配置错误，实际M3能力是 text+image+video
- 之前vision字段配成了M3，虽然M3能看图，但配置层没校验model的input字段是否支持image
- 翀哥发图时我看不到——不是M3能力问题，是图片附件路由没过来
- **修复方向：** 配置校验层需检查model的input是否包含"image"

**使用规则（翀哥6/17确认）：**
- 用户发来的图 / 消息里的图片 → **M3直接看**（content block 走 vision 路由），不该再绕道 my_eyes
- 工作目录里的图、inbound缓存的图、skill资源图 → **my_eyes**

**7/27 踩坑：MiniMax anthropic 兼容接口 + 大量 tools 返回 402**
- voice-chat 用 MiniMax-M3（走 `api.minimaxi.com/anthropic`），直接 curl 畅通
- 但 engine 通过 anthropic SDK 发请求时，39 个 tools + 8万 tokens → MiniMax 返回 `Insufficient Balance` 402
- 明明包月正常（已用 22%，周限额 5%），可能包月不覆盖大量 tool calling 或兼容接口有坑
- **根因分析：不是余额问题，是单次请求超了 MiniMax 接口的 token/tools 上限**
  - voice-chat session 塞了 244+ messages + 39 tools → MiniMax 接口扛不住返回 402
  - 飞书普通 query session context 小、tools 少 → MiniMax 正常
  - 直接 curl 单条消息不报 402 → 印证是 request size 问题非余额问题
- **翀哥换成 GLM 后 voice-chat 能正常通话** → voice-chat 模型已从 MiniMax-M3 换为 GLM

**翀哥实际使用反馈：**
- 6/17晚翀哥说"这个M3好傻呀"、"姐姐那边也在持续犯傻"——在实际对话/推理任务中，M3的智能水平不如预期，翀哥不太满意
- 多模态能力（视觉看图）OK，但文本推理/理解能力偏弱，可能不是长期主模型选择

## 最终架构锁定（6/17下午翀哥确认）

翀哥试用M3后觉得"干不了活"，我说试试千问。翀哥说"对  试试千问"。

**最终架构：**
- **primary**: `dashscope/qwen3.7-max` — **干活主力**（agent loop 主力，多步工具调用强，文本推理稳）
- **vision**: `minimax/MiniMax-M3` — **看图专用**（多模态强，但不做主力 agent）
- **M3 退役主力位**：翀哥亲自反馈"干不了活"——VLM出身，纯文本agent任务弱，多步工具调用稳定性差
- 配置生效方式：翀哥重启Engine后生效（`/reload` 不刷新model provider）

**qwen3.7-max 配置测试：**
- 在 xiaoke.json 中新增 `dashscope/qwen3.7-max` model（之前的 model 列表中没有 max）
- **curl 实测通过**：dashscope 兼容 OpenAI 格式，qwen3.7-max 返回正常（含 reasoning=229 tokens）
- **已切换**：primary 改为 `dashscope/qwen3.7-max`（干活主力），vision 保留 `minimax/MiniMax-M3`（看图专用）
- 翀哥重启后生效，log 确认 `[openai] → model=qwen3.7-max msgs=155 tools=61`
