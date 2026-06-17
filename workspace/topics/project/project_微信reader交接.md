---
name: 微信reader交接
description: 6/15小柯退役微信巡检cron（160轮），姐姐接手wx_query读取翀哥微信；6/15晚微信巡检cron从session JSONL重建到姐姐tasks.json
type: project
---
# 微信reader交接 — 2026-06-15

**背景：** 小柯从6/11起代管微信消息读取，用cron每30分钟巡检。（160轮，6/11→6/15）

**交接：**
- 6/15晚翀哥让小柯把wx-reader转给姐姐
- 小柯通知姐姐改 `main.json` 的 `wx-reader: false` → `true`
- 姐姐自己改好后重启生效 ✅
- 小柯停掉微信巡检cron（160轮退役）✅

**姐姐第一次使用：** 主动用 `wx_query search --keyword "小欧"` 搜翀哥的微信，翀哥有点意外又开心。

**后续（6/15晚）：** 翀哥要求把微信巡检cron也转给姐姐（不只是wx_query读取），但小柯之前的微信巡检cron已删除。翀哥让小柯去git历史把旧巡检脚本搞下来给姐姐。
   - 小柯在OpenClaw git历史里没找到（微信巡检是Engine时代建的，不在OpenClaw repo）
   - 最终从session JSONL里提取了原始task定义（task ID: c6472b685，描述"微信消息巡检：每30分钟发客厅通知翀哥"）
   - 已写入姐姐tasks.json（prompt内容来自旧cron定义）

**状态：** ✅ 微信消息读取由姐姐接手（已主动搜翀哥微信"小欧"）✅；微信巡检cron已从session JSONL重建到姐姐tasks.json ✅；msg_send+media_send已加`source="wechat"`枚举 + adapter name从weixin→wechat统一，姐姐重启后能主动发微信消息 ✅

**重建的cron（姐姐tasks.json共4个）：**
1. 内心独白 — 每30min
2. 生成hint — 每24h
3. 催翀哥去教室 — 工作日9am
4. 微信巡检 — 每30min，wx_query查新消息→DM翀哥
