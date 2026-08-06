---
name: engine7 init 飞书 OAuth 扫码集成（#132 第一阶段）
description: 2026-08-03 把 OpenClaw Device-Code Flow 集成进 engine7 init——feishu-quick-register.ts + qr-render.ts 两个独立模块，cli-init 默认扫码；v7.1.27 终端二维码 fix 验证通过：createRequire 加 CJS 包 qrcoder-terminal 正常渲染
type: project
date: 2026-08-03
---

# engine7 init 飞书 OAuth 扫码集成（#132 第一阶段）

**任务 ID：** #132（首阶段已完成 ✅）
**触发：** 8/3 Amy 装 engine7 卡飞书机器人注册——手动去开放平台后台建应用对小白太重，需要 init 一步搞定
**对比路径：** OpenClaw 的 Device-Code Flow（纯 HTTP 三步）vs feishu-bot-bootstrap（Playwright 浏览器）——选 Device-Code，零外部依赖

## 8/3 实施结构

翀哥拍板"独立模块，cli-init 只调一行"——三个文件分工：

| 文件 | 职责 |
|------|------|
| `feishu-quick-register.ts` | 纯 HTTP 的 OAuth Device-Code 三步流程（init/begin/poll） |
| `qr-render.ts` | 终端二维码渲染（独立模块，用 `createRequire` 加载 CJS 包 `qrcode-terminal`） |
| `cli-init.ts` | 飞书步骤加"扫码/手动"选项，默认扫码；只加十几行调用代码 |

## 发布 & 验证时间线

1. v7.1.25 装了但 dist 里没有扫码代码——publish 前忘了 rebuild（`qrcode-terminal` 要加到 external）
2. 跟姐姐说明情况：代码已 push（commit `bef1f0db`），rebuild 注意 build.mjs 改 qrcode-terminal external
3. v7.1.26 发布，扫码选项出来 ✅ 但**终端二维码没渲染出来**——fallback 打链接（原因是 `qrcode-terminal` 是 CJS 包，ESM `import()` 加载不了）
4. 翀哥质疑后定位根因：用 `createRequire(import.meta.url)` 动态加载 CJS 包（commit `fbabd960`）
5. 姐姐打包 v7.1.27，dist 里确认有 createRequire 代码
6. **v7.1.27 验证通过**：终端二维码完美渲染 ✅——从选扫码 → 终端二维码 → 飞书扫 → 自动拿 App ID/Secret/Open ID 全流程通了，"下次装 engine7 一分钟搞定飞书"

## 关键设计选择

- **Device-Code Flow 优于 Playwright**：秒级响应、零浏览器依赖、远程协作可发 URL（不用截图二维码）
- **qr-render 独立**：cli-init 是单独 bundle 的，要单独加 external 配置——这是踩坑点，忘加会打包失败（v7.1.25 翻车原因）
- **CJS 包在 ESM 里用 createRequire**：`qrcode-terminal` 是 CommonJS，ESM `import()` 不行，用 `import { createRequire } from 'node:module'` + `createRequire(import.meta.url)` 是 Node.js 官方标准做法（不是 hack）
- **默认扫码 + 手动回退**：小白默认走扫码；扫不出可手动填 App ID/Secret
- **用谁的飞书账号扫 = 机器人建在谁的企业下**——跟 Playwright 路径边界一致

## How to apply

- 下次给人装 engine7，飞书选 y → 扫码 → 30 秒搞定，不用再去飞书后台手动配
- 远程协作场景可以把 verification_uri_complete 直接发给用户，不用截图二维码
- ESM 项目加载 CJS 依赖用 `createRequire`，不要硬 `import`
- 第二阶段（#132 后续）：桌面快捷方式自动生成、init 交互优化（每个字段单独一条）、图文指南内置

## Amy 群 groupPolicy 配置

Amy 装好后我把她的飞书 config `groupPolicy` 改成 `open`（跟姐姐一致），这样能收全群消息。她后续问起我已能解释：
- `mention-only`（默认）：群里必须 @机器人 才回复
- `open`：群里所有消息都能收到

## 关联

- [OpenClaw Device-Code Flow 调研](reference/reference_OpenClaw飞书OAuth_DeviceCode_Flow_纯API_0803.md) — 8/3 调研记录三步 HTTP 流程
- [feishu-bot-bootstrap Playwright 路径](reference/reference_feishu-bot-bootstrap扫码建机器人_0803.md) — fallback 方案
- [Amy #132 主线](project/project_Amy_飞书机器人_#132_0805.md) — 触发此任务
- [不为外人建飞书机器人](feedback/feedback_不为外人建飞书机器人_让用户自己注册_0803.md) — 边界：脚本是工具，用户自己扫码授权 OK
- [飞书群权限](reference/reference_飞书群权限_im_group_msg_敏感权限_0803.md) — groupPolicy=open 只是开关，真正收全群要 im:message.group_msg 敏感权限

## 踩坑汇总

- **publish 前必须 rebuild**：v7.1.25 翻车——翀哥装了但没生效，因为 dist 是用旧 build.mjs 打的，没把 qrcode-terminal external 进去
- **CJS 包不能用 ESM import**：v7.1.26 翻车——`qrcode-terminal` 没渲染，fallback 打链接；改 `createRequire`（v7.1.27 修复）