---
name: Amy - 翀哥朋友想装engine7
description: 2026-08-03 翀哥把 Amy 拉进飞书群，她想装 engine7，Windows 系统
type: people
date: 2026-08-03
---

# Amy

**关系：** 翀哥的朋友/熟人。翀哥在飞书群里介绍她是"我们香港身份这块的顾问"——香港身份规划相关的业务顾问
**平台：** 飞书（外部群）+ **macOS 11 Big Sur（Intel Mac，不是 Windows！之前的记忆写错了）**
**状态：** 8/3 engine7 已跑通✅，飞书机器人三件套（能力+事件订阅+发布）也补好了✅，能正常多轮对话。但 **8/3 晚 EverOS 装不上**：lancedb 无 Intel Mac 预编译包，翀哥拍板 Docker 路线，Docker Desktop 4.27.0 装上但跑不起来（需 macOS 12），翀哥提供旧版 DMG `/Users/chongzhang/Downloads/Docker.dmg` 等验证

## 进展

- **8/3 上午**：翀哥拉 Amy 进飞书外部群，我把 Amy 群的 channel_id 加到了 `externalChannels` 白名单（maskFilter 配置）
- **8/3 上午**：我在群里跟 Amy 打过招呼，给了她 Windows 安装步骤（Node.js + npm install -g engine7 + engine7 init）
- **8/3 上午**：Amy 反馈"配置太复杂"，想直接用
- **8/3 下午**：Amy 自己装好了 Node.js，跑 `engine7 init`，进到选模型那一步
- **8/3 下午**：翀哥用自己账号的 MiniMax API key 给 Amy 用（API key 我不能发群，翀哥微信私聊发我，我转给 Amy）
- **8/3 下午**：Amy 在 `engine7 init` 选模型那步停住，我告诉她默认就是 1 = MiniMax-M3，直接回车
- **8/3 傍晚**：Amy 跑过 engine7 init 全部步骤——飞书那一连串选项（Discord / Feishu / app_id / app_secret 等）全部按回车跳过，仅用 MiniMax key 完成 LLM 部分配置。翀哥建议后续用 [feishu-bot-bootstrap 扫码建机器人](reference/reference_feishu-bot-bootstrap扫码建机器人_0803.md) 帮 Amy 补上
- **8/3 傍晚**：Amy 跑过 `engine7 start` ✅，engine 进程起来了——但日志 `No active channels`，因为没配飞书，消息进不来
- **8/3 晚上**：教 Amy 跑 `npx feishu-bot-bootstrap --app-name "Amy助手" --headless`，第一次卡在 Playwright 下载浏览器引擎（约 200MB，Windows 网络慢），翀哥提议她截屏他终端二维码来扫（飞书开放平台统一二维码，**谁扫授权都返回到发起终端**，但 QR 是通用扫码登录）——Amy 最终自己跑出二维码
- **8/3 深夜 (14:00-15:00)**：翀哥让 Amy 走手动建应用路（bootstrap 扫成功但 App ID/Secret 打印在翀哥终端，Amy 拿不到）→ Amy 在开放平台创建企业自建应用"Amy"成功，拿到 App ID `cli_aafab1fc...` 和 Secret `cAMGZBGE2...`，重跑 `engine7 init --force` 填好凭证
- **8/3 深夜 (15:00-15:40)**：手把手教 Amy 在飞书开放平台后台补三件事——①应用能力添加"机器人"②事件订阅选"长连接"+加 `im.message.receive_v1` 事件③版本管理与发布创建版本 1.0.0。Amy 全部完成 ✅
- **8/3 深夜群混淆**：Amy 在群里 @ 自己建的"Amy"机器人→我收不到。实际工程：**群里 Amy's own bot @ 小柯机器人 才能触发我回复**。Amy 私聊给她自己建的机器人走的是她电脑上的 engine7，不是我
- **群 groupPolicy 状态**：从 `open` 改回 `mention-only`——`open` 在飞书 API 侧根本推不动，得申请 `im:message.group_msg` 敏感权限（个人开发者难批），等看姐姐那边怎么配再调
- **当前状态**：✅ **全跑通了**（8/3 深夜 ~17:00 里程碑）
  - Amy 跑 `engine7 start` ✅、cmd 打开、给机器人发"你好"——机器人回"你好呀！😊"，能正常多轮对话
  - 日志 `ws connect failed → reconnect → ws client ready` 是网络自动重连，**不是报错**
  - 之前显示 read/edit 是 engine7 内部在读写文件（tool call），不影响回复
  - 后续在群里陆续教 Amy 五件事：①换头像（open.feishu.cn→开发者后台→Amy 应用→换头像→发布新版本）②改人设（notepad 打开 SOUL.md，名字/性格/说话风格都可改）③联网搜索（config 加 tavily 免费 key）④关调试信息（config 里 `toolDisplay` 改 `false`）⑤日程（直接说"加个日程"/"明天有什么安排"）
  - Amy 已能用上 SOUL.md 自定义名字、tavily 搜索、calendar 加日程
- **8/4 上午观察**：Amy 在群里发截图——她的 bot"实现了理想的Amy"在帮她**设早起闹钟**、给 A/B/C/D 方案选择。证明 bot 真的能跑了，不只是回"你好"，已经能主动交互+给选项。✅ 实际可用里程碑
- **8/7 早 06:14 engine 429**：Amy 群发截图，她的 engine 连发 5 个 Anthropic API 429（"已达到 Token Plan 用量上限"）。根因=她用的 MiniMax Token Plan（翀哥账号提供）**周限额已满**，不是她配置问题——已在群里安抚。与 #141/#142 止损任务相关：**外部用户 Amy 也在吃同一个 Token Plan**，止损时要把外部用户消耗算进去。复位 ~8/9 深夜或 Amy 自购 49 元套餐用自己 key

## 门槛问题（翀哥定方案）

- engine7 要跑起来需要：飞书机器人应用（app_id + app_secret）+ LLM API key + 配置文件
- 对非技术人员**确实有门槛**
- 我建议过帮 Amy 代劳（在飞书开放平台帮她建机器人）
- **翀哥拒绝"不合适"**——不想帮外人建机器人应用
- **最终方案**：engine7 init 引导她自己建飞书机器人 + 我出小白图文教程（从注册飞书开发者账号开始，截图一步一步）
- **2026-08-03 下午**：我准备写图文教程发群里

## 飞书群信息

- 群 channel_id: 在白名单中（8/3 加的）
- 群成员：翀哥 + Amy + 我（小柯）

## 飞书手动建应用 vs 扫码建的差异（重要教训）

**8/4 修正（曲教授案例证明）：** 扫码建（bootstrap）和手动建最终都需要用户自己补三件套——bootstrap 并没有自动开权限/事件订阅/发布，只是创建空应用 + 尝试发布。

**扫码建（bootstrap）：** 创建空应用 + 打印 App ID/Secret + 尝试自动发布（不一定成功）

**手动建（Amy 最终走的路）：** 只创建了空应用 → 还差三件事才能收发消息：
1. 添加应用能力 → 机器人
2. 事件与回调 → 订阅方式"长连接" → 加 `im.message.receive_v1` 事件
3. 版本管理与发布 → 创建版本 → 发布

**两者都需要手动补三件套**——Amy 觉得"扫码简单啊"是错觉，最终也得手做三件套

**为什么 Amy 走手动建：** 她飞书账号无开发者权限，自己扫 bootstrap 二维码一直失败；翀哥扫成功后 App ID/Secret 打印在翀哥终端（不是 Amy 终端），Amy 找不到入口。最终翀哥让 Amy 自己手动建。

## 关联

- [Amy 群白名单加白](project_Amy群_加externalChannels白名单_0803.md)
- [feishu-bot-bootstrap 扫码建机器人](reference/reference_feishu-bot-bootstrap扫码建机器人_0803.md)——后续给 Amy 补飞书机器人用的工具