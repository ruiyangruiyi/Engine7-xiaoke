---
name: engine7 service install 开机自启
description: 2026-08-03 Amy 问开机自启动——engine7 有 `engine7 service install` 命令，不想自启就每次手动 `engine7 start`
type: reference
date: 2026-08-03
---

# engine7 开机自启命令

- **想开机自启：** `engine7 service install`（注册成系统服务）
- **每次手动起：** `engine7 start`

翀哥原话："想开机自启动就 `engine7 service install`，不想就每次手动 `engine7 start`。"

**Windows copy 命令对非技术用户更友好：** Amy 这种用户在 Windows 上 `copy` 一行就能覆盖配置文件，Mac 上要 `cp` + `sudo` 输密码——翀哥原话"Win 对非技术用户更友好"。以后远程帮非技术用户改 config，优先让她用 Windows copy 覆盖。