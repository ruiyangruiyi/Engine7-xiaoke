---
type: feedback
created: 2026-07-01
tags: [bash, wsl, voice-chat, findShell, bug]
---

# findShell WSL fallback bug (7/1)

## 问题
`findShell()` (BashTool.ts L45-92) 在 Windows 上用 `where.exe bash` 找 bash。如果返回的全是 WSL bash（被 `isWslBash()` 过滤掉），旧代码会 fallback 到 `candidates[0]`——但那也是 WSL bash。

WSL bash 里没装 python → voice-chat 的 Python 子进程 crash（`python: command not found`）。

## 根因
这台机器 `where.exe bash` 返回两个 WSL bash：
- `C:\Windows\System32\bash.exe`
- `C:\Users\24045\AppData\Local\Microsoft\WindowsApps\bash.exe`

Git Bash 存在（`C:\Program Files\Git\bin\bash.exe`）但不在 PATH 里，所以 `where.exe` 找不到它。

## 为什么之前能跑
代码从 5/29 没改过。可能是 Windows 更新/重启后 PATH 变了，导致 `where.exe bash` 不再返回 Git Bash。

## 修复
去掉 `candidates[0]` fallback（不 fallback 到 WSL bash），让 findShell 走 knownPaths 找 Git Bash。这样不依赖 PATH。

## 教训
- findShell 的 knownPaths fallback 是必要的——不能假设 PATH 里有 non-WSL bash
- **永远不要 fallback 到 WSL bash**——WSL 环境和 Windows 环境的工具链不同
