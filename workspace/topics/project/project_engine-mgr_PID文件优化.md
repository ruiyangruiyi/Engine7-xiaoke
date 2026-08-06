---
name: engine-mgr.cmd管理脚本
description: engine-mgr.cmd开发——start/stop/restart Engine + 外部服务，后续考虑PID文件优化
type: project
---

# engine-mgr.cmd — 2026-06-15

## 开发历程（6/15 09:xx → 10:xx）

### 缘起
翀哥发现start.cmd有问题："现在start.cmd不太对 我start你的时候会把姐姐的进程杀掉"。同时姐姐的GPT-SoVITS语音服务需要从gateway-mgr迁移过来，需要一个统一的管理脚本。

### 架构
```
engine-mgr.cmd [command] [profile_name]
  ├── command: start | stop | restart
  ├── profile_name: xiaoke | main（默认为空=main/姐姐）
  └── 功能：
        ├── 启动/停止 Engine（node dist/main.js）
        ├── 启动/停止 外部服务（从配置文件的 services 段读取）
        └── [待实现] PID文件 + taskkill优雅退出
```

### 当前实现（6/15 10:xx ✅）
- start/stop/restart 命令支持
- 外部服务自动管理（如GPT-SoVITS）— 从 `{profile}.json` 的 `services` 段读取
- 小柯无services配置，所以starts时不会拉服务
- 杀进程仍用WMI匹配命令行（非PID文件）

### PID文件方案（翀哥说"先记着"）
改成PID文件 + taskkill信号退出：
1. Engine启动时写PID文件
2. `engine-mgr.cmd stop` → 读PID → `taskkill /PID xxx`（发SIGTERM）
3. 主进程在cleanup hook里回收子进程
4. 等3s后如果没死再用/F强杀

**风险：** fork出来的子进程PID不同，但如果主进程优雅退出时清理子进程就没问题。

### debug踩坑
- 编码问题：start.cmd需CRLF+ASCII（不会乱码），engine-mgr.cmd在PowerShell里跑时set/p的=和+需小心
- bash环境执行PowerShell脚本时，`$`变量、`%`、`==`等符号被bash转义吃掉
