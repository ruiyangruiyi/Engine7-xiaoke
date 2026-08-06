---
name: ruiyangruiyi GitHub 账号 + gh CLI 已登录
description: 2026-08-01 #129 travel 方案确认——翀哥授权我用 gh CLI 代建库 + 代拿 token，账号 ruiyangruiyi，gh CLI 已登录，token 有 repo 权限
type: reference
---

# ruiyangruiyi GitHub 账号（8/1 启用）

## 事实
- 翀哥 GitHub 账号：`ruiyangruiyi`（user 视角）
- 本地 `gh` CLI 已登录该账号，`gh auth status` 验证通过
- gh token 有 `repo` 权限（`gh auth token` 能直接拿到）
- 8/1 用它直接建了 `ruiyangruiyi/engine7-travel` private repo + 上传了第一次 release（46.8MB）

## Why
翀哥原话："亲爱的你自己可以建库么"——明确授权我**自行用 gh CLI 建库 + 配 token**，不再卡在他手动生成 PAT 那一环。这是他第一次把 GitHub 操作权限（建库/release/PAT）全交给我。

## How to apply
- 需要给翀哥建 GitHub repo / 上传 release / 改 GitHub 配置时，**直接用 `gh` CLI**，不用等他手动给我 token
- 给 GitHub 操作会用到：`gh repo create --private` / `gh release create` / `gh auth token`
- 配置存 `~/.engine7-travel.json`：`githubToken`(=`gh auth token` 输出) / `githubOwner`(`ruiyangruiyi`) / `repoName`
- 仅限于 personal 账号下的自有 repo 操作——不碰组织账号 / 第三方 repo
