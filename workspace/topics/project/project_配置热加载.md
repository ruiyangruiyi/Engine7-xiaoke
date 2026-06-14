---
name: xiaoke.json配置热加载
description: Engine配置热加载已实现，Discord输入/reload即可刷新配置
type: project
---

**实现：** `/reload` slash命令，重新读取xiaoke.json，热刷新以下配置，无需重启Engine：
- recall/extract provider（换模型不用重启）
- topics配置
- display配置
- autoDream配置
- features开关
- providers列表
- ⚠️ **preview颜色**（previewColor/previewTemplate）**不可热加载**——颜色在adapter初始化时传入，`/reload`只刷新config对象，不会重建adapter

**颜色配置（6/13新增）：**
- Discord：`channels.discord.previewColor: 13941396`（奶茶色0xD4A574的十进制）
- 飞书：`channels.feishu.previewTemplate: "orange"`（最接近奶茶色的飞书预设）
- 不配则用默认（Discord蓝0x5865F2 / 飞书黄yellow）

**生效：** 重启Engine后，Discord DM里输入`/reload`即可。飞书/其他平台暂不支持（仅Discord slash命令）。

**背景：** 翀哥6/13提出需求，xiaoke.json改完后要重启才能生效太麻烦，希望改成热加载。

### CC可帮重启Engine（6/13验证）
- **6/13翀哥在车里直播时，让CC帮忙重启Engine**
- CC操作：kill旧node进程 → `npx tsx src/main.ts` 启动新进程
- 成功使所有改动生效（三个tool、preview颜色、DM slash命令等）
- **注意：** 不要擅自重启网关（feedback已有），翀哥明确指示才能操作
- ⚠️ **CC重启必须走脚本，不能自己发明命令：** CC用 `npx tsx src/main.ts` 启动后，脚本（rebuild.cmd/start.cmd）找不到进程，又拉起一个，导致双进程。两个小柯同时跑→消息发两遍、team建两次、跟姐姐循环聊天。6/13晚翀哥发现后指出。正确做法：用 `start.cmd` 或 `rebuild.cmd` 启动。
