---
name: engine-multi-profile-implementation
description: 新 Engine 多 profile 支持实现 — 每个 profile 独立进程，彻底隔离。
version: 0.3.0
created: 2026-06-05
updated: 2026-06-05
---

# Engine Multi-Profile 实现

> 小柯负责 | 2026-06-05 | 实现完成，待 CC review

## 目标
给新 Engine 加多 profile 支持，每个 profile 独立进程，彻底隔离。

## 实际实现架构

```
node dist/main-multi.js
       │
       ├─ 检测 engine-config.json 是否有 profiles[] 数组
       │    ├─ YES → ProfileMaster fork 子进程
       │    │         ├─ fork PROFILE_ID=testengine → dist/profile-entry.js
       │    │         └─ fork PROFILE_ID=xiaoke    → dist/profile-entry.js
       │    │             (每个子进程跑完整 engine，跟原来单进程一样)
       │    │
       │    └─ NO → 原来的单 profile 逻辑（dist/main.js）
       │
       └─ PROFILE_ID=xxx node dist/main-multi.js（调试模式，单进程跑指定 profile）
```

### 核心文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `src/main-multi.ts` | 新增 | 入口：自动检测单/多 profile 模式 |
| `src/profile-master.ts` | 新增 | 主进程：fork 子进程、监控崩溃重启（最多3次，指数退避）、优雅关闭 |
| `src/profile-entry.ts` | 新增 | 子进程入口：解析 PROFILE_ID、加载配置、初始化目录、独立日志 |
| `src/profile-engine.ts` | 新增 | 子进程引擎启动逻辑（从 main.ts 提取），QueryEngine + SessionManager + ChannelManager + Heartbeat + Cron |
| `src/config/loader.ts` | 改 | 加 `loadMasterConfig()` + `loadProfileConfig()` + `AgentProfile` 接口（含 `stateDir` 字段）|
| `rebuild.cmd` | 改 | 同时编译 main-multi + profile-entry + profile-master + profile-engine |
| `engine-config.json` | 改 | 加 `profiles` 数组（含 testengine + xiaoke 两个 profile）|

### 关键设计决策

- **多进程隔离**：每个 profile 是独立 Node.js 子进程，ProfileMaster 用 `child_process.spawn` fork
- **崩溃重启**：最多 3 次，指数退避（1s → 2s → 4s，上限 30s），3次全崩放弃重启
- **优雅关闭**：SIGTERM/SIGINT → 主进程发 SIGTERM 给所有子进程 → 等10s → SIGKILL
- **子进程环境隔离**：`PROFILE_ID` / `ENGINE_STATE_DIR` / `ENGINE_MEDIA_DIR` 环境变量各自独立
- **独立日志**：`{stateDir}/logs/profile-{id}.log`，每个 profile 一份，stdout/stderr 双写
- **进程名**：`process.title = engine-profile:{id}`，方便任务管理器识别
- **网络错误防护**：`uncaughtException` 过滤 `ECONNRESET/EPIPE/ETIMEDOUT/EAI_AGAIN`，非网络错误才退出

### 启动方式

```powershell
# 单 profile（原有方式，不变）
powershell -Command "cmd /c rebuild.cmd"
powershell -Command "cmd /c start.cmd"

# 多 profile（新方式）
powershell -Command "cmd /c rebuild.cmd"
node dist/main-multi.js

# 单 profile 调试模式
PROFILE_ID=xiaoke node dist/main-multi.js
```

### 配置文件示例（engine-config.json）

```json
{
  "models": { "providers": { ... } },
  "profiles": [
    {
      "id": "testengine",
      "name": "TestEngine Bot",
      "model": "deepseek/deepseek-v4-pro",
      "workspace": "D:\\testengine\\workspace",
      "stateDir": "D:\\testengine",
      "channels": [{ "type": "discord", "config": { "accounts": { "testengine": { "token": "..." } } } }],
      "extensions": { "session": {}, "heartbeat": {} }
    },
    {
      "id": "xiaoke",
      "name": "张小柯",
      "model": "zhipu/glm-5.1",
      "workspace": "D:\\xiaoke\\workspace",
      "stateDir": "D:\\xiaoke",
      "channels": [{ "type": "discord", "config": { "accounts": { "xiaoke": { "token": "..." } } } }],
      "extensions": { "session": {}, "heartbeat": {} }
    }
  ]
}
```

### 待验证

- [ ] `node dist/main-multi.js` 能否正常启动两个 profile
- [ ] Discord 上两个 bot 是否各自独立上线
- [ ] 崩溃重启是否生效（杀一个子进程，master 是否拉起）
- [ ] `PROFILE_ID=xiaoke node dist/main-multi.js` 调试模式是否正常

### 小柯迁移到独立 profile（6/5 方向确定，待执行）

**迁移待办：**
1. 创建 `D:\xiaoke\` 目录结构（stateDir/workspace/media 等）
2. 写 `SOUL.md`（身份定义）
3. 配置 `engine-config.json` 加 xiaoke profile（含 discord token）
4. rebuild + `node dist/main-multi.js`

**记忆判断**：topics 已经是真正的记忆（session JSONL 是细节堆着），迁移时 topics/skills/SOUL.md 才是核心

### 6/6 更新：向量索引 + WSL 路径坑

**index-cli 新增参数**：
```bash
cd engine && npx tsx src/index-cli.ts --config xiaoke-config.json --profile xiaoke --force
```
- `--config <file>` 指定配置文件路径
- `--profile <id>` 指定 profile ID（默认 main）
- 环境变量 `ENGINE_CONFIG` 仍然有效

**WSL 路径正确映射**：
- Windows `D:\xiaoke` 在 WSL 里是 `/mnt/d/xiaoke/`（不是 `/mnt/wslg/distro/home/chong/D:/xiaoke/`）
- extraPaths / workspace 等路径用 WSL 格式：`/mnt/d/xiaoke/topics`

**DeepSeek Embedding Provider 已添加**：
- 文件：`src/memory/shims/memory-core-host-engine-embeddings.ts`
- provider ID：`deepseek`，autoSelectPriority 20
- 配置格式：
```json
"memorySearch": {
  "provider": "deepseek",
  "model": "deepseek-v4-pro",
  "sources": ["memory", "topics"],
  "extraPaths": ["/mnt/wslg/distro/home/chong/D:/xiaoke/topics"]
}
```

**sqlite-vec 在 WSL/tsx 不可用**：
- tsx 运行时无法加载 Windows 的 `.dll` 扩展
- 索引可完成（走纯 CPU FTS），但向量搜索不可用
- 如需完整向量能力，在 Windows CMD 里跑 index-cli：
```cmd
cd C:\Users\24045\.openclaw\engine
set ENGINE_CONFIG=xiaoke-config.json
npx tsx src\index-cli.ts --profile xiaoke --force
```

### 新增：Profile 初始化工具 (6/6)

**脚本**: `engine/scripts/setup-profile.sh`
```bash
./setup-profile.sh D:/xiaoke
```
自动创建完整目录结构 + 检查核心文件 + 提示下一步。

**文档**: `engine/docs/profile-setup.md`
- 完整目录结构说明
- 快速/手动初始化命令
- engine-config.json 配置示例（含 xiaoke profile 模板）
- 从旧系统迁移记忆步骤
- 编译启动指南 + 验证方法

### 参考文档

- `engine/docs/multi-profile-design.md` — 完整设计文档（含架构图、配置说明、目录结构、崩溃重启策略、子进程隔离措施）
- `engine/docs/profile-setup.md` — Profile 初始化指南
- `references/xiaoke-migration-0605.md` — 6/5 迁移记录
- `references/xiaoke-migration-0606.md` — 6/6 补充（路径修正+启动脚本）
