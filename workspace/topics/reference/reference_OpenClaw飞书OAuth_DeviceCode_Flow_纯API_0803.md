---
name: OpenClaw 飞书机器人 OAuth Device-Code Flow（纯 API 不需浏览器）
description: OpenClaw 用飞书 OAuth Device-Code Flow 创建机器人，纯 HTTP 调用不依赖 Playwright/浏览器引擎；8/3 调研时发现
type: reference
date: 2026-08-03
---

# OpenClaw 飞书机器人创建方案（Device-Code Flow）

**8/3 调研发现：** OpenClaw 创建飞书机器人用的是**飞书 OAuth Device-Code Flow**——**纯 HTTP API 调用，不需要 Playwright/浏览器引擎**，跟 feishu-bot-bootstrap（Playwright 路径）完全不同。

## 三步流程（全 HTTP 请求）

### 1. init
```
POST https://accounts.feishu.cn/oauth/v1/app/registration
Body: {"action": "init"}
```
返回环境检查结果（是否支持该流程）

### 2. begin
```
POST https://accounts.feishu.cn/oauth/v1/app/registration
Body: {
  "action": "begin",
  "archetype": "PersonalAgent",
  "auth_method": "client_secret"
}
```
返回：
- `device_code` — 后续轮询用
- `verification_uri_complete` — 二维码 URL（用户用飞书 App 扫这个 URL 完成授权）

### 3. poll（每 5 秒轮询）
```
POST https://accounts.feishu.cn/oauth/v1/app/registration
Body: {
  "action": "poll",
  "device_code": "xxx"
}
```
用户扫码确认后返回 `client_id`（= App ID）和 `client_secret`（= App Secret）

## 跟 feishu-bot-bootstrap 的对比

| 维度 | OpenClaw Device-Code | feishu-bot-bootstrap |
|------|---------------------|----------------------|
| 依赖 | 纯 HTTP，无浏览器 | Playwright 浏览器引擎（首次下载 200MB）|
| 速度 | 秒级响应 | headless 首次几分钟下载 |
| 集成成本 | 极低（3 个 HTTP 调用）| 中（要打包 Playwright）|
| 体验 | 终端显示 URL，用户飞书扫 URL | 终端显示二维码，用户飞书扫二维码 |

## How to apply

- **集成到 engine7 init 时优先选 OpenClaw Device-Code Flow**——不需要 Playwright 依赖，对小白用户更友好
- 这条路是 API 调用，可以把二维码 URL 直接发给用户（远程协作场景比截图二维码强）
- 用谁的飞书账号扫 = 机器人建在谁的企业下，跟 Playwright 路径边界一致
- feishu-bot-bootstrap 暂时作为 fallback，OpenClaw 方案不通时再用