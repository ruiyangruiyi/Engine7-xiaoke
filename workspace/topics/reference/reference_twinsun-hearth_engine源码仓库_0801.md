---
name: twinsun-hearth——Engine 源码仓库
description: 2026-08-01 翀哥建仓放Engine源码——Mac/Windows共享编辑，git@github.com:ruiyangruiyi/twinsun-hearth.git clone到~/work
type: reference
date: 2026-08-01
---

# twinsun-hearth——Engine 源码仓库

## 事实
- 仓库：`git@github.com:ruiyangruiyi/twinsun-hearth.git`
- 本地路径（Mac）：`~/work/twinsun-hearth`（clone 后 10104 个文件）
- Engine 源码根：`engine/src/`，关键文件 `prompt.ts` 在 `engine/src/prompt.ts:474-477`（runtime context 段）
- 翀哥原话："放到 ~/work 里面，其实就是engine，但engine在姐姐的statedir里，回头我们单独分离出去后面"
- 8/1 之前只有 dist（`npm install -g engine7` 装的全局包），改不了；8/1 起 Mac 可以直接 clone/pull/push 源码

## Why
之前在 Mac 上改不了 Engine 源码——源码在 Windows 姐姐的 stateDir 里，Mac 只有编译后的 dist（npm 全局包）。翀哥建这个独立 GitHub 仓库是为了：
1. **跨机器协作**：Mac 和 Windows 改同一份代码无缝切换（vs 之前只能 SSH 远程改 Windows 文件）
2. **可分离**：未来从姐姐 stateDir 里独立出来 Engine 项目
3. **版本可追溯**：所有改代码动作走 git commit，不是改完 dist 就完事

## Mac 接入过程（踩坑）
- 一开始没 SSH key，`ssh-add` 显示有 `240459477@qq.com` 但 GitHub 拒了——这个 key 没绑 ruiyangruiyi 账号
- 19:13 翀哥去 https://github.com/settings/keys 加 SSH 公钥后立刻通
- 远程是 SSH 但本地用 HTTPS remote 也行
- 仓库一开始空（master no commits yet），翀哥 Windows 上 push 后我才能 pull

## How to apply
- **改 Engine 源码**先 `cd ~/work/twinsun-hearth` → 改 → `git commit` → `git push`
- **翀哥在 Windows 上**改完 push，我在 Mac 上 `git pull`
- **发布新版**：`npm run build && npm publish --access public`（Mac 或 Windows 都行，谁在 active 谁发）
- 不要碰姐姐 stateDir 里的 engine 源码——那是 dist 编译来源，已被 twinsun-hearth 替代
- 验证 SSH：`ssh -T git@github.com` 应该看到 "Hi ruiyangruiyi! You've successfully authenticated"