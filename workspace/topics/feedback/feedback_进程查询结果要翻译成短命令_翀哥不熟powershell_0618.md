---
name: Windows进程查询结果要翻译成短命令——翀哥不熟PowerShell
description: 6/18 11:15翀哥飞书承认"我在windows都不知道怎么看 powershell哪些命令太恶心了太长记不住"——以后查Windows进程/服务/网络状态要把PowerShell翻译成短可执行命令给他，不要甩长WMI/Get-WmiObject串
type: feedback
date: 2026-06-18
---
6/18 11:15 翀哥飞书原话：
> "我在windows在都不知道怎么看  powershell哪些命令太恶心了太长记不住"

## 背景

11:11 我自己跑 start.cmd 把 engine 杀了，翀哥从飞书发我"你自己把自己退了"。我跟他解释"看到的 node 进程是 playwright mcp + claude code + 两个 engine + 一些 MCP 子进程"——他追"怎么有那么多 看看有几个你"。

我给的是 tasklist / Get-WmiObject 的长 WMI 命令筛选结果，**他看不懂 PowerShell**。

## 这次学到的

1. **翀哥不熟 PowerShell 也不熟 Windows 命令**——他的强项是 JS/Node 架构逻辑、glman、调度、模型切换；Windows 本地进程/服务管理是盲区
2. **给我"信息"时要翻译**——我查到"PID 66252 是小柯 engine，CommandLine 含 xiaoke.json + dist\main.js"是给我自己看的信息；给翀哥要翻译成"小柯 engine = 进程名为 node + 命令行含 xiaoke.json 那个"
3. **短命令优先**——他能记住的：`tasklist`、`taskkill /pid xxx`、`netstat -ano | findstr :port`、`sc query 服务名`、`Get-Service` 名字（这也算短）。长的 `Get-WmiObject Win32_Process -Filter "..."` 他记不住
4. **不甩链接**——"你去搜 PowerShell 怎么看进程"= 推责。直接给"用 tasklist 看所有 node 进程"这种话

## Why

1. **他 11:13 飞书发"你自己把自己退了"**——他不能本地复盘 = 我必须做他的"Windows 翻译层"。他给方向我执行，进程细节我转译
2. **我之前查进程都直接贴 Get-WmiObject 串**——翀哥没反馈过他看不懂，但我**没意识到**他看完是懵的
3. **5/11 教训"不要自己重启 engine"叠加**——他不熟 PowerShell + 我自己重启 = 双重风险。**以后查 Windows 进程我直接给"用 X 命令能看"这种**短指令

## How to apply

1. **查 Windows 进程时**：用 `tasklist` + `findstr` 过滤 → 给翀哥的是"看进程用 tasklist /fi \"imagename eq node.exe\""这种**短命令模板**，不是 wmic 长串
2. **查特定进程命令行**：`wmic process where "name='node.exe'" get CommandLine,ProcessId /format:list` 太长 → 用 PowerShell 短版 `Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Select-Object ProcessId, CommandLine`（如果非用不可）→ **或者直接 grep tasklist 输出**
3. **查端口占用**：`netstat -ano | findstr :端口号` → 短、好记
4. **杀进程**：`taskkill /pid PID /f` → 翀哥能直接复制跑
5. **不要给翀哥一坨 PowerShell pipeline**——他自己跑了报错 = 我得远程 debug，浪费时间。先用 Linux 习惯的 tasklist 给结果，他要细节再上 PowerShell
6. **WSL bash 下查 Windows 进程**：用 `tasklist.exe`（直接调 exe）比 `powershell.exe -Command "..."` 稳——前者不跨 PowerShell 边界，后者跨边界会静默失败（参考 feedback_自己跑start_cmd杀engine_wsl_powershell踩坑_0618.md）
