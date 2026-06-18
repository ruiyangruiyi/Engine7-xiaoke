---
name: PowerShell速查表
description: 6/18 11:15翀哥飞书"我在windows在都不知道怎么看 powershell哪些命令太恶心了太长记不住"——他要我整理一份PowerShell速查表到docs/sop/
type: project
date: 2026-06-18
---
6/18 11:15 翀哥飞书原话：
> "我在windows在都不知道怎么看  powershell哪些命令太恶心了太长记不住"

他想让我**整理一份 PowerShell 速查表**到 `D:/xiaoke/workspace/docs/sop/`，以后忘了直接查。

## 应该包含的命令（结合今天上午实战）

- `tasklist /FI "IMAGENAME eq node.exe"` —— 看所有 node 进程
- `tasklist /V /FI "PID eq <pid>"` —— 看某个 PID 的详情（含 CommandLine + StartTime）
- `taskkill /F /PID <pid>` —— 强杀进程
- `Get-Process node | Select-Object Id, StartTime, @{Name="Cmd";Expression={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine}}` —— 看 node 进程的启动时间+命令行
- `Get-WmiObject Win32_Process -Filter "Name='node.exe'" | Select-Object ProcessId, CommandLine, CreationDate` —— 旧版 WMI 方式（WSL 跨边界不稳）
- `Get-CimInstance Win32_Process -Filter "Name='node.exe'"` —— 新版 CIM 方式
- `where.exe <command>` —— 找命令路径
- `Get-Command <name>` —— 查命令类型/源
- `Get-Help <command> -Examples` —— 查用法+示例
- `Get-Process | Where-Object {$_.ProcessName -eq "node"} | Stop-Process -Force` —— PowerShell 风格杀进程

## Why

翀哥在 Windows 上不熟 PowerShell（已知 C/C++ 主语言，对 shell 操作有距离）。今天上午我用 `tasklist`、`wmic`、start.cmd 等都靠记忆和猜——他看着费劲。**他自己也想学怎么直接看进程状态**，不想每次都依赖我（我是 LLM，需要查询+输出，延迟比直接看高很多）。

## How to apply

1. 写到 `D:/xiaoke/workspace/docs/sop/powershell_cheatsheet.md`
2. 结构：**场景→命令→解释→示例输出**
3. 重点放**今天用过的真实命令**（tasklist / taskkill / wmic / Get-Process）
4. 标 WSL bash 下调 PowerShell 的坑（`Get-WmiObject` 跨边界可能静默失败）
5. 写完发飞书/Discord 给翀哥看
