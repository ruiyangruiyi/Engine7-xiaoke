# engine7 init 集成 feishu-bot-bootstrap 扫码创建飞书机器人

## 背景

Amy 装 engine7 时卡在飞书 App ID/Secret 步骤——非技术人员不知道怎么建飞书机器人。
feishu-bot-bootstrap（npm 包）可以扫码自动创建飞书机器人应用，30秒拿到 App ID/Secret。

## 目标

engine7 init 里加一个选项："扫码自动创建飞书机器人"
→ 内部调 feishu-bot-bootstrap → 终端打印二维码 → 用户飞书扫码 → 自动拿到凭证 → 写入 config

## 实现方案

1. engine7 init 飞书配置步骤加选项："手动输入 / 扫码创建"
2. 选"扫码创建" → `npx feishu-bot-bootstrap --app-name "engine7" --headless`
3. 终端显示二维码，用户飞书扫码
4. 拿到 App ID/Secret 后自动填入 config
5. 提示用户在飞书里搜索机器人名称，发条消息触发配对

## 依赖

- feishu-bot-bootstrap（npm 全局包，已验证可用）
- Playwright 无头浏览器（feishu-bot-bootstrap 内部依赖，首次运行自动下载）

## 源码位置

- feishu-bot-bootstrap 源码：~/work/feishun-bot-bootstrap/
- 核心流程：src/flow.ts（扫码→创建应用→开权限→发布→提取凭证）
- engine7 cli-init：engine/src/cli-init.ts（飞书配置步骤在 line 244-249）

## 额外优化（非技术用户体验）

1. **桌面快捷方式**：engine7 init 完成后自动在桌面生成"启动Engine7.bat"，双击即可启动
2. **安装包内置 .bat**：npm 包里带 start.bat 模板，init 时拷到桌面
3. **init 交互优化**：Discord/飞书字段提示更清晰，避免填混
4. **图文安装指南**：生成 PPT/PDF 格式的安装备忘录（md 非技术用户打不开）

