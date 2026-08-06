---
name: feishu-bot-bootstrap 工具
description: npx feishu-bot-bootstrap --app-name "名字" --headless 通过扫码自动创建飞书机器人应用并返回 app_id/app_secret
type: reference
date: 2026-08-03
---

# feishu-bot-bootstrap

**工具命令：**
```
# 模式1（headless，默认下载 Playwright 浏览器引擎）
npx feishu-bot-bootstrap --app-name "Amy助手" --headless

# 模式2（非 headless，用本机 Chrome/Edge）
npx feishu-bot-bootstrap --app-name "Amy助手"
```

**用法：** 终端跑命令 → 弹出二维码 → 飞书扫码 → 30秒自动创建机器人应用 → 返回 App ID/Secret 填回 engine7 init

**8/3 Amy 案例：**
- 翀哥最初认为 engine7 没有扫码建飞书机器人的能力
- 我提醒有这个工具（--headless 模式不需要手动打开浏览器）
- 适合分享给非技术朋友体验时一键建机器人

**踩坑（实测 Amy Windows）：**
- **首次 --headless 模式会下载 Playwright 浏览器引擎（约200MB）**，Windows 网络慢要等几分钟
- **超过3分钟还在转就 Ctrl+C，换非 headless 模式**（用本机 Chrome/Edge，省下载）
- **远程协作工作流**：翀哥在自己电脑跑命令 → 终端出二维码 → 翀哥截图发给 Amy → Amy 用她飞书 App 扫 → 扫完后 App ID/Secret 会打印在翀哥的终端里 → 翀哥把 App ID/Secret 转给 Amy
  - 关键：因为是飞书开放平台统一登录二维码，谁扫都授权同一个账号
  - 不需要在 Amy 电脑上生成二维码（在翀哥电脑上生成也能授权扫）

**注意：**
- 扫码时是**用谁的飞书账号**这个机器人就建在**谁的企业下**——[feedback_不为外人建飞书机器人](feedback/feedback_不为外人建飞书机器人_让用户自己注册_0803.md) 仍然是边界，不能用翀哥账号扫码帮外人建
- 让用户自己扫码 = 用户自己建在自己企业下，符合边界

**重要修正（8/4 曲教授案例踩坑）：**
- bootstrap 扫码**只创建了空应用**（拿到 App ID/Secret），**并没有自动配权限、事件订阅、版本发布**——跟手动创建应用一样，机器人还是不能收发消息
- 之前 Amy 案例里"扫码建=自动开机器人能力+导入权限+配事件订阅+尝试发布"的描述不准确，实际没做这些事（只是尝试了发布，但因为账号无开发者权限发布失败）
- **结论**：无论扫码还是手动建，**都必须用户自己在飞书开放平台后台补三件套**才能收发消息（@see reference_飞书应用收发消息权限_三件套_0803）：
  1. 应用能力 → 添加"机器人"
  2. 事件与回调 → 订阅方式"长连接" → 加 `im.message.receive_v1` 事件
  3. 版本管理与发布 → 创建版本 1.0.0 → 发布
- #132（8/5）把 bootstrap 集成进 init 时需要增强为**自动补三件套**——否则外行人装完也是哑的