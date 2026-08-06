---
name: workspace/research/EverOS 是 submodule——别往里 commit
description: 2026-08-04 清理 git 时踩坑——workspace/research/EverOS 是指向上游官方仓库的 submodule，我没权限也没法 push，但昨天研究时往里面 commit 了部署文件，submodule HEAD 指向一个上游不存在的本地 commit，父仓库一旦推到别处 clone 就拉不下来
type: reference
date: 2026-08-04
---

# workspace/research/EverOS 是 submodule——别往里 commit

8/4 16:50 翀哥问我"有没有没提交的改动"时我答错了——昨天研究 EverOS 部署时我在 `workspace/research/EverOS` 里面新建了 Dockerfile / start.sh / agentic-server / ollama-bin 等文件，还 commit 了（8bac7fc）。但这个目录是个 git submodule，origin 指向 **上游 EverOS 官方仓库**——我没权限 push 上去，国内到 GitHub 还超时。

## 坑在哪

- submodule HEAD 指向一个**只在本地的 commit**（8bac7fc），上游根本没有
- 父仓库的 commit 引用了这个不存在的 submodule ref，**推到别处 clone 会直接拉不下来**（submodule 找不到 ref）
- 我之前没意识到 submodule 的 origin 是上游，还当成普通目录往里 commit

## 怎么修

- submodule revert 回上游 HEAD（`git -C workspace/research/EverOS reset --hard <upstream-HEAD>`）
- 父仓库重新 commit 把 submodule ref 指回合法值
- 我新建的部署文件**没 commit 也没 push**，备份到 `/Users/chongzhang/work/everos-deploy/`（仓库外）留作日后用
- 85M 的 ollama-bin 绝对不能 commit（也不该进 git），通过 `build.sh` 说明怎么获取

## Why

- 父仓库里 submodule 的 ref 必须**上游真实存在**——子模块的 commit 不是私有 commit，是上游仓库 commit 的引用
- 任何要"存到仓库里"的东西，先进父仓库的 docs/deploy 目录，不进 submodule
- submodule 是"借来的代码"，不是"我的代码"——别在里面改东西

## How to apply

- 看到 `.gitmodules` 文件 → 这个目录是 submodule，改前先看 `git config --get submodule.<name>.url`
- 在 submodule 里新加文件想 commit → **先问翀哥**：这个改动要不要进父仓库？通常进父仓库的 `docs/<name>-deploy/` 或 `research/<name>/` 目录
- 父仓库 commit 前快速 sanity check：`git -C <submodule> log --oneline -1` 确认 submodule HEAD 在上游存在；`git status` 干净
- 大文件（>1MB）→ 一律不进 git，本地放或 `.gitignore` + 文档说明获取方式
