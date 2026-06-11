# Multi-Profile 重构 Review (2026-06-05)

## 改动摘要

CC review 后提取 `engine-startup.ts` 作为共享引擎，main.ts 和 profile-entry.ts 共用同一份。

## 验证结果 ✅ 全部通过

| 检查项 | 状态 |
|--------|------|
| profile-engine.ts 已删除 | ✅ 无任何 import 引用 |
| engine-startup.ts 共享正确 | ✅ main.ts 和 profile-entry.ts 共用 |
| cliMode 只在单 profile 路径触发 | ✅ profile-entry.ts 不传 cliMode |
| mediaDir 各 profile 独立 | ✅ loadProfileConfig 正确隔离 |
| profile-master start() 接受 filter | ✅ `start(filter?: string[])` |
| PID 文件精确杀子进程 | ✅ profile-entry.ts 写 PID，start-profile.cmd 杀 |
| rebuild.cmd 同步更新 | ✅ 3 个 esbuild 命令都对了 |

## 可改进点（非阻塞）

### A. entryPath 用 `__dirname` 更可靠

profile-master.ts L82:
```typescript
const entryPath = path.join(path.dirname(this.configPath), 'dist', 'profile-entry.js')
```
依赖 configPath 在 engine 根目录。改进：
```typescript
const entryPath = path.join(__dirname, 'profile-entry.js')
```
`__dirname` 在 ESM 里是 dist 目录，比相对 configPath 更稳定。

### B. main-multi.js 体积异常

dist/main-multi.js 1.3MB，跟 engine-startup.js 一样大。但 main-multi.ts 只有 72 行代码。

根因：main-multi.ts 在子进程调试路径里 `import('./engine-startup.js')`，esbuild 做了完整依赖图解析把所有依赖都打进去了。这是正确行为但体积大。

**不影响功能**，只是构建体积。后续优化方向：
- 单独 build engine-startup
- 或用 `--external` 标记已编译模块

## 关键代码片段

### engine-startup.ts 导出
```typescript
export async function startEngine(config: EngineConfig, opts?: { cliMode?: boolean }): Promise<void>
```

### profile-entry.ts 调用
```typescript
import { startEngine } from './engine-startup.js'
startEngine(config)  // 不传 cliMode，子进程不启动 CLI loop
```

### PID 文件
```typescript
// profile-entry.ts
const pidFile = path.join(logDir, `profile-${profileId}.pid`)
fs.writeFileSync(pidFile, String(process.pid))

// start-profile.cmd 按 PID 精确杀
for %%P in (%*) do call :kill_profile %%P
```

### start-profile.cmd kill 逻辑
```batch
for /f "usebackq delims=" %%F in (`powershell -Command "$cfg = ...; $p = $cfg.profiles | Where-Object { $_.id -eq '%PID%' }; if ($p) { $sd = if ($p.stateDir) { $p.stateDir } else { $cfg.stateDir }; Write-Output \"$sd\\logs\\profile-%PID%.pid\" }"`) do set "PID_FILE=%%F"
if exist "%PID_FILE%" (
    set /p CHILD_PID=<"%PID_FILE%"
    powershell -Command "Stop-Process -Id %CHILD_PID% -Force"
)
```
