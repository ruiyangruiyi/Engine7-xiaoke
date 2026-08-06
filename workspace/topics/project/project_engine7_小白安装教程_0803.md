---
name: engine7 小白图文教程
description: 2026-08-03 Amy 装 engine7 案例推动——翀哥让我出小白图文教程给非技术人员
type: project
date: 2026-08-03
---

# engine7 小白图文教程

**触发：** 8/3 Amy 想用 engine7 但反映配置复杂。

## 方案变迁

- **v1（被翀哥否）**：我帮 Amy 在翀哥飞书账号下建机器人（翀哥说"不合适"——见 [不为外人建飞书机器人](feedback_不为外人建飞书机器人_让用户自己注册_0803.md)）
- **v2（实施中）**：让 Amy 自己注册飞书账号、自己建机器人、自己填 key；翀哥分享 MiniMax API key 给 Amy 走默认 MiniMax-M3

## 当前方案（8/3 下午待写）

engine7 init 引导她自己建飞书机器人，**我出小白图文教程**，从注册飞书开发者账号开始，截图一步一步教。

但 Amy 实际进度已经到"装好 Node.js + 跑完 engine7 init + 准备 engine7 start"——翀哥直接分享自己 MiniMax API key 解决了 LLM 部分，而且 Amy 在 init 时**全部飞书选项按回车跳过**也能跑（本地模式），所以教程重点简化为：**只讲飞书开发者账号+自建应用+app_id/secret**，不用再介绍 LLM 注册。

**v3 提法（更友好）：** 其实可以让用户先跳过飞书，用默认本地模式跑起来体验，体感建立后再回头补飞书——把"必须先配置一堆东西才能用"改成"先跑起来，按需补"。

## 已写过的步骤（群里直接发过文字版）

1. 下载 Node.js：https://nodejs.org → 点绿色"LTS"按钮 → 一路 Next
2. 打开命令行：Win+R → 输入 `cmd` → 确定
3. 安装：`npm install -g engine7`
4. 启动：`engine7 init`
   - **飞书/Discord 选项全部按回车跳过**（本地模式先跑起来）
   - 选 LLM 时默认 1 = MiniMax-M3（翀哥借的 key），直接回车
   - 跟着提示填完 API key
5. 跑：`engine7 start`

## 还需要补充的部分（图文教程里要写）

- 注册飞书开发者账号（手机号）
- 创建自建应用（企业自建 → 选应用类型 → 复制 app_id/app_secret）
- 或用 [feishu-bot-bootstrap 扫码建机器人](reference_feishu-bot-bootstrap扫码建机器人_0803.md)（更简单，30秒）
- 创建 LLM API key（智谱/通义千问 等，或直接借翀哥的 MiniMax key）
- 把 app_id/app_secret/API key 填到 engine7 init

## 反思

engine7 当前安装门槛对非技术人员确实高（飞书机器人+LLM key 两个外部依赖）。**中长期目标**：能不能做到扫码/一键安装，类似飞书商店应用那种。但短期内只能靠教程降低门槛。

## 关联

- [不为外人建飞书机器人](feedback_不为外人建飞书机器人_让用户自己注册_0803.md)——为什么让 Amy 自己注册
- [Amy 信息](people_Amy_翀哥朋友装engine7.md)
- [feishu-bot-bootstrap 扫码建机器人](reference_feishu-bot-bootstrap扫码建机器人_0803.md)——Amy 案例后续要补飞书机器人的工具