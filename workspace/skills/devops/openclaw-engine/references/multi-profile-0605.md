# Multi-Profile 支持实现 (2026-06-05)

> 小柯实现 | 每个 profile 独立进程，彻底隔离

## 架构

```
node dist/main-multi.js
       │
       ├─ 检测 engine-config.json 是否有 profiles[] 数组
       │    ├─ YES → ProfileMaster fork 子进程
       │    │         ├─ fork PROFILE_ID=testengine → dist/profile-entry.js
       │    │         └─ fork PROFILE_ID=xiaoke    → dist/profile-entry.js
       │    │             (每个子进程跑完整 engine，独立 stateDir)
       │    │
       │    └─ NO → 原来的单 profile 逻辑（dist/main.js）
       │
       └─ PROFILE_ID=xxx（调试模式，单进程跑指定 profile）
```

## 新增文件

| 文件 | 说明 |
|------|------|
| `src/main-multi.ts` | 多 profile 入口（检测 profiles 数组路由） |
| `src/profile-engine.ts` | 从 main.ts 提取的 engine 启动逻辑（子进程用） |
| `src/profile-entry.ts` | 子进程入口（设置环境变量、日志、启动 engine） |
| `src/profile-master.ts` | 进程管理（fork/监控/重启/关闭） |

## 改动的文件

| 文件 | 改动 |
|------|------|
| `src/config/loader.ts` | 加 `EngineMasterConfig` + `loadMasterConfig()` + `loadProfileConfig()` |
| `rebuild.cmd` | 同时编译 main-multi.ts + profile 系列文件 |

## 配置格式

```json
{
  "models": { "providers": { ... } },
  "profiles": [
    {
      "id": "testengine",
      "name": "TestEngine Bot",
      "model": "deepseek/deepseek-v4-pro",
      "workspace": "D:/testengine/workspace",
      "stateDir": "D:/testengine",
      "features": { ... },
      "channels": [{ "type": "discord", "config": {} }]
    },
    {
      "id": "xiaoke",
      "name": "张小柯",
      "model": "zhipu/glm-5v-turbo",
      "workspace": "/Users/chongzhang/xiaoke/workspace",
      "stateDir": "/Users/chongzhang/xiaoke/",
      "features": { ... },
      "channels": [{ "type": "discord", "config": {} }]
    }
  ]
}
```

## 关键设计

### 隔离点
- 每个 profile 独立 `stateDir` → 独立 `sessions/` + `memory/` + `logs/` + `state.db`
- 独立进程 → 一个崩溃不影响其他
- 崩溃重启：最多 3 次，指数退避（1s → 2s → 4s，上限 30s）

### 编译
```bash
cd /mnt/c/Users/24045/.openclaw/engine
cmd.exe /c "rebuild.cmd"
```

### 启动
```bash
# 多 profile 模式
node dist/main-multi.js

# 单 profile 调试
PROFILE_ID=xiaoke node dist/main-multi.js
```

## 踩过的坑

1. **main.ts 不能条件导入**：TypeScript 的 `import` 是静态的，不能放在 `if` 里。解决方案：新建 `main-multi.ts` 作为独立入口，不动原有 `main.ts`。

2. **rebuild.cmd 只打包 main.ts**：esbuild 不会自动包含新增的 `.ts` 文件。必须在 rebuild.cmd 里显式加每个新文件的 `--bundle` 命令。

3. **子进程日志要透传**：stdout/stderr 通过 `proc.stdout?.on('data')` 透传到父进程终端，否则看不到子进程输出。

4. **Windows cmd 乱码**：从 bash 里调用 `cmd //c rebuild.cmd` 会乱码，必须套 `powershell -Command "cmd /c ..."`。

## 待验证

- [ ] 子进程崩溃后重启是否正常
- [ ] 优雅关闭时所有子进程是否正确退出
- [ ] Discord 消息是否正确路由到对应 profile
- [ ] 不同 profile 的 sessions/memory 是否完全隔离
