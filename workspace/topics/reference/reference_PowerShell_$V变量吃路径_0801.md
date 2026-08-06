---
name: PowerShell路径含$变量名被吃
description: 2026-08-01 翀哥删~$VoiceChat_Live.pptx踩坑——PowerShell/cmd都把路径里的$V当变量吃了；用LiteralPath或Get-ChildItem管道才解决
type: reference
date: 2026-08-01
---

# PowerShell 路径含 `$` 变量名被吃（Office 临时锁文件踩坑）

## 事实
翀哥要删 `D:\xiaoke\workspace\docs\pitch\~$VoiceChat_Live.pptx`（Office 异常关闭残留），三种方式都失败：

```powershell
# 失败 1：del 双引号 —— $V 被当变量，路径变成 ~.pptx
PS> del "D:\xiaoke\workspace\docs\pitch\~$VoiceChat_Live.pptx"
del : 找不到路径"D:\xiaoke\workspace\docs\pitch\~.pptx"

# 失败 2：Remove-Item 单引号 —— 文件被 Office 进程锁（不是 $V 问题）
PS> Remove-Item 'D:\xiaoke\workspace\docs\pitch\~$VoiceChat_Live.pptx'
Remove-Item : 无法删除项 ... 你没有足够的访问权限执行此操作

# 失败 3：cmd /c 双引号 —— cmd 也吃 $V
PS> cmd /c "del /f /q D:\xiaoke\workspace\docs\pitch\~$VoiceChat_Live.pptx"
找不到 D:\xiaoke\workspace\docs\pitch\~$VoiceChat_Live.pptx
```

## 解决方案
```powershell
# 方案 A：LiteralPath 参数（不走 wildcard 解析）
Remove-Item -LiteralPath 'D:\xiaoke\workspace\docs\pitch\~$VoiceChat_Live.pptx' -Force

# 方案 B：批量管道（最稳）
Get-ChildItem -Path 'D:\xiaoke' -Recurse -Filter '~$*' | Remove-Item -LiteralPath { $_.FullName } -Force

# 方案 C：cmd 转义（不推荐）
del /f /q "D:\xiaoke\workspace\docs\pitch\~^$VoiceChat_Live.pptx"
```

## Why
PowerShell 双引号字符串里 `$` 是变量前缀，`$VoiceChat_Live` 被解析成空变量变成 `.pptx`。单引号不走变量解析但 Office 进程锁了文件导致 EPERM。cmd.exe 里 `$` 不是变量但 cmd 对引号里的 `$` 也处理得不一致。

`LiteralPath` 参数告诉 cmdlet "这是字面字符串，不要 wildcard/变量解析"，最稳。

## How to apply
- **任何 Windows 路径含 `$`**：必须用单引号 + `-LiteralPath` 参数
- **批量删 Office 临时文件**：`Get-ChildItem -Recurse -Filter '~$*' | Remove-Item -LiteralPath { $_.FullName } -Force`
- **不要相信 PowerShell 双引号字符串**直接传路径，特别是 `$`、`%`、`!` 这类特殊字符
- **cmd 转义**用 `^`，PowerShell 转义用 `` ` ``——记混会再踩坑