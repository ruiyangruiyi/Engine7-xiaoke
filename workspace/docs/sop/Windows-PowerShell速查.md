---
name: Windows PowerShell 速查（翀哥专用）
description: 6/18 11:15 翀哥说"我在windows在都不知道怎么看  powershell哪些命令太恶心了太长记不住"——把常用 PowerShell 命令整理成速查
type: knowledge
date: 2026-06-18
---

# Windows PowerShell 速查

> 翀哥原话："我在windows在都不知道怎么看  powershell哪些命令太恶心了太长记不住"
>
> 整理日常 Engine/MCP/Node 进程排查用到的 PS 命令，附"为什么这么写"。

---

## 1. 查进程

### 查所有 node 进程（含 CommandLine）
```powershell
wmic process where "name='node.exe'" get ProcessId,ParentProcessId,CommandLine /format:list
```
- `wmic` = WMI 命令行，老牌但 Windows 8/10/11 都有
- `where "name='node.exe'"` 过滤只看 node
- `get ProcessId,ParentProcessId,CommandLine` 要哪些列
- `/format:list` 列展示（默认是表格，太宽会换行看不全）

### 查某 CommandLine 匹配的进程（找 engine / MCP）
```powershell
wmic process where "name='node.exe' and CommandLine like '%xiaoke.json%'" get ProcessId,CommandLine /format:list
```
- `like '%xxx%'` 模糊匹配
- 整段 where 子句要双引号，shell 不会拆

### 看进程树（谁拉起了谁）
```powershell
wmic process where "ProcessId=66252" get ProcessId,ParentProcessId,CommandLine,CreationDate /format:list
```
- 用拿到的 PID 反查父进程
- `CreationDate` 看进程启动时间（格式 `20260618111348.392258+480` = 2026-06-18 11:13:48 +8时区）

### 简单看（不需要 CommandLine）
```powershell
tasklist | findstr node
```
- `tasklist` 类似 Linux 的 `ps aux`，但是 Windows
- `findstr` = grep 的 Windows 版
- 看 PID 够用，CommandLine 看不到

---

## 2. 杀进程

### 杀单个 PID
```powershell
Stop-Process -Id 66252 -Force
```
- `-Force` 强制（不发 SIGTERM，直接 KILL）

### 杀一批（按 CommandLine 匹配）
```powershell
Get-WmiObject Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -like '*xiaoke.json*' -and $_.CommandLine -like '*dist*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```
- `Get-WmiObject Win32_Process` = 查所有进程
- `Where-Object { ... }` = 过滤（PowerShell 的 where）
- `ForEach-Object { ... }` = 遍历（PowerShell 的 for）
- `$_` = 当前对象（类比 shell 的 `$0` / `it`）

### 替代写法（更短）
```powershell
Get-Process node | Where-Object { $_.Path -like '*xiaoke*' } | Stop-Process -Force
```
- `Get-Process node` 只看 node
- 但 `Get-Process` 拿不到 CommandLine，所以要找 CommandLine 还是用 `Get-WmiObject`

---

## 3. 看文件

### 看日志（实时）
```powershell
Get-Content /Users/chongzhang/xiaoke/\logs\engine-2026-06-18.log -Wait
```
- `Get-Content` = cat
- `-Wait` = `tail -f`

### 看日志（最后 50 行）
```powershell
Get-Content /Users/chongzhang/xiaoke/\logs\engine-2026-06-18.log -Tail 50
```
- `-Tail 50` 类似 `tail -n 50`

### 找日志里的关键词
```powershell
Select-String -Path /Users/chongzhang/xiaoke/\logs\engine-2026-06-18.log -Pattern "API returned empty"
```
- `Select-String` = grep
- `-Pattern` 关键词

---

## 4. 快捷组合

### 一行：找 engine PID + 杀
```powershell
Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like '*xiaoke.json*' -and $_.CommandLine -like '*dist*' } | ForEach-Object { Write-Host "PID=$($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force }
```

### 一行：列出所有 engine + 路径
```powershell
wmic process where "name='node.exe' and CommandLine like '%configs%'" get ProcessId,CommandLine /format:list
```

### 一行：算 node 进程数
```powershell
(Get-Process node).Count
```

---

## 5. 必坑点

### 1. `Get-WmiObject` 在 WSL 调 PowerShell 时偶尔不工作
- WSL → `powershell.exe -Command "Get-WmiObject ..."` 跨边界，可能拿不到结果
- 替代：`tasklist` 或者 `wmic`（wmic 跨边界更稳）

### 2. 路径里的 `\` 在 PowerShell 里要转义
- `/Users/chongzhang/xiaoke/\logs\...` 直接写没问题
- 但在 `-like` 模式里要写 `'*xiaoke.json*'`（单引号包裹），不要双引号包双引号

### 3. `wmic` 在 Windows 11 22H2+ 默认不再预装
- 如果 `wmic` 找不到，用 `Get-CimInstance` 替代：
  ```powershell
  Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" | Select-Object ProcessId, CommandLine
  ```
- `Get-CimInstance` 是新版 API，等价于 `Get-WmiObject`

### 4. 管道符 `|` 在 PowerShell 里传递的是**对象**不是字符串
- `Get-Process | Where-Object` 传的是 Process 对象，不是文本
- 想当文本用 `| Out-String`

### 5. PowerShell 默认编码是 GBK
- **跨进程传中文/emoji 不要用 stdin/stdout**，用文件（详 [feedback_post