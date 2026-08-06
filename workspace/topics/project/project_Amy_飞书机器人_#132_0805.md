---
name: Amy 飞书机器人扫码创建 #132
description: 2026-08-03 Amy engine7 跑起来后卡在补飞书机器人，#132 排到 8/5；Amy 账号无开发者权限扫码失败，最终翀哥帮扫
type: project
date: 2026-08-03
---

# Amy 飞书机器人扫码创建

**任务 ID：** #132
**排期：** 2026-08-05（跟 #75/#79/#131 同批）
**触发：** 8/3 傍晚 Amy 的 engine7 已成功跑起来，但日志显示 `No active channels`——因为飞书那一连串选项全跳过，没 app_id/app_secret，消息根本进不来

**8/3 晚进展（11:00-12:40）：**
- Amy 新开 cmd 窗口后跑 `feishu-bot-bootstrap --headless`
- Amy 自己扫二维码一直失败（可能账号无开发者权限 / 二维码过期）
- Ctrl+C 重跑也不行
- 翀哥直接用自己的飞书账号扫了码——bootstrap 自动跑完了建应用+开权限+配事件订阅
- **bootstrap 打印的 App ID/Secret 在翀哥终端，Amy 这边没拿到**——不是 bootstrap 没成功，是 Amy 那边需要引导她去开放平台后台查

**8/3 深夜（13:00-13:40）Amy 拿到了凭证：**
- 路径：Amy 自己进飞书开放平台开发者后台 → "创建企业自建应用" → 填 "Amy" → 进应用 → "凭证与基础信息"
- App ID：`cli_aafab1fc93389cd3`
- App Secret：`cAMGZBGE2IG8TlfvmKANibl7Dfz5OudV`
- 备注：bootstrap 已经建好的应用后台应该也在，只是 Amy 没找到入口（她当时在"创建新应用"页面上）

**8/3 深夜继续（13:40-15:00）重跑 init 卡死：**
- Amy 跑 `engine7 init` 想重新配飞书凭证，但 init 检测到 `.engine7` 配置目录已存在**直接 return**——根本没有 --force 或 reconfigure 选项
- 帮 Amy 手动 `rmdir /s /q C:\Users\EDY\.engine7` 清掉目录 → `engine7 init` 成功进入配置流程
- Amy 现在的状态：agent 名 Amy、飞书凭证填好、open_id 跳过——重跑成功！

**新增功能 `engine7 init --force`（8/3 晚）：**
- 触发：Amy 这次卡 init 没有任何重配选项，发现 engine7 init 缺这个能力
- 改的代码：`engine7 init` 加 `--force` 参数，命中时跳过 `.engine7` 已存在检查直接重配
- commit：`014de0e2`
- 已 push，Amy 那边等 npm 版更新才能用——目前手动 `rmdir /s /q` 是 fallback
- help 文本也同步更新了

**翀哥拍板后续方向：**
- 把 bootstrap 扫码建机器人**集成进 engine7 init**——Amy 这种用户扫一下就全搞定，不用手动去开放平台建
- 这个集成任务排到 #132（8/5），跟 #75/#79/#131 同批

**要做的事：**
1. ✅ Amy init 跑完 + 凭证填好（8/3 深夜）
2. ✅ Amy 飞书后台的**权限 + 事件订阅 + 发布**（8/3 凌晨全手动建完）
3. ✅ Amy engine7 start 跑起来 + feishu Connected（8/3 凌晨 Windows 端）
4. 🔄 Amy 发消息给机器人没回复——**根因：飞书应用缺 im:message.send / im:message.send_as_bot 权限**（8/3 凌晨已定位）
   - 解决路径：飞书开放平台 → Amy 应用 → 权限管理 → 用"批量导入/导出权限"一次性开 im:message.* 全家桶 → 创建新版本发布
   - **8/3 深夜最新进展**：Amy 通过批量导入 JSON 的方式把权限都加进去了，下一步是点"发布"按钮——等 Amy 验证机器人能否正常回复

**8/3 凌晨（16:00）发布卡点：**
- Amy 把权限加进去后点"保存并发布"被飞书弹窗打回——要求**版本号必须比上次的大**
- 我让 Amy 在"版本管理"里新建版本号填 **1.1.0**（比之前默认的 1.0.0 大就行）
- 填完保存，等一两分钟给机器人发消息测试
- 等 Amy 发布后回来验证
5. ✅ Amy 群 groupPolicy:open + 敏感权限开通——**8/3 晚翀哥办完 im:message.group_msg 后群里不用 @ 也能收到消息**
   - 验证：Amy 群里发消息我没被 @ 也收到了；apply 文档已记（[reference_飞书群权限_im_group_msg_敏感权限_0803]）
   - 这条从"卡住"到"打通"，是 #132 案例傍晚的最后一关
6. #132（8/5）：把 feishu-bot-bootstrap 集成进 engine7 init 流

**8/3 深夜（~17:00-18:00）新增 #132 改进项：**

翀哥建议——engine7 init 完成后**自动在桌面生成快捷方式**（.bat 双击启动），不用每次开 cmd。我把下面三项都写进 #132 方案里了：

1. **桌面快捷方式自动生成**：init 完成后在 `%USERPROFILE%\Desktop\` 创建 `engine7.bat` 双击启动
2. **init 交互优化**：每个字段单独一条引导、字段名+示例值贴出来（参考 Amy 三次填反的教训）
3. **图文指南内置**：init 流程里嵌入分步截图指引，参考 [engine7 小白图文教程]

**8/3 深夜（17:30）Amy 拿到的 engine7.bat：**
- 单文件 .bat，Amy 下载到桌面双击即启动 engine7，不用开 cmd
- 已发群里给 Amy

**踩坑（记给未来）：**
- Amy 飞书账号没有开发者权限，自己扫不了二维码——这是普通用户的常见卡点，不是工具的问题
- 二维码可能过期——刷不出来让 Ctrl+C 重跑
- 教程发群里要**一步一行发，不给选择**（Amy 选不动）

**前置依赖：**
- Amy 自己电脑跑命令（npx 会自动下载）
- 第一次会卡 Playwright 浏览器引擎下载（~200MB），给 fallback：去掉 `--headless`
- 飞书 App 扫码授权（需要开发者权限的账号）

**8/3 深夜（~16:30）里程碑——消息链终于通了：**
- Amy 发布权限后测试，发"你好"——engine7 **真的回了一个工具调用**（edit SESSION-STATE），不是空回复
- 这说明：飞书三件套（权限/事件订阅/app_id-secret）全配齐了 → Amy 飞书机器人 ✅ 收消息 ✅ 发消息 ✅
- 但回复内容是 edit 文件而非聊天——**是 engine7 的 prompt 配置问题**，不是飞书通道问题
- 我让 Amy 先 /stop 或 Ctrl+C 重启稳住；翀哥回 Windows 后帮她调 SOUL.md
- 结论：8/3 一整天的 Amy 装 engine7 案例——从 0 到能收发消息已经走完 ✅

**关联：**
- [Amy 信息](people_Amy_翀哥朋友装engine7.md)
- [feishu-bot-bootstrap 扫码建机器人](reference/reference_feishu-bot-bootstrap扫码建机器人_0803.md)
- [engine7 小白图文教程](project/project_engine7_小白安装教程_0803.md)
- [不为外人建飞书机器人](feedback/feedback_不为外人建飞书机器人_让用户自己注册_0803.md) — 边界依然在（机器人不能帮外人"建"，但"扫码授权"是另一层——翀哥用自己账号扫朋友该走的官方授权，OK）
