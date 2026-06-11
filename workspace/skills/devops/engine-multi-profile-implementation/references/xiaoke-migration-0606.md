# 小柯 Migration 进度 (6/6 补充)

## 记忆文件位置

**正确路径**：`/mnt/d/xiaoke/`（WSL可写）
包含：MEMORY.md (7437字节，最新)、SOUL.md (2202字节)、USER.md (3640字节)、topics/ (19个)、skills/ (全部)、memory/ (daily/docs/scripts)

> ⚠️ 之前错误写成 `/mnt/wslg/distro/home/chong/D:/xiaoke/`，实际是可写的 `/mnt/d/xiaoke/`

## 配置文件位置

**主配置**：`/mnt/c/Users/24045/.openclaw/engine/configs/xiaoke.json`（完整profile配置）
**索引配置**：`/mnt/c/Users/24045/.openclaw/engine/xiaoke-config.json`（仅含memorySearch）

**目录结构**：
```
configs/
  xiaoke.json       ← 主配置（含profile完整定义）
  testengine.json
xiaoke-config.json  ← 向量索引专用（仅memorySearch+provider）
```

## 启动脚本

- `start_xiaoke.cmd` — 启动小柯profile，杀旧进程后跑 `node dist/main-multi.js --profile xiaoke`
- `start_multi.cmd` — 通用多profile启动，可传参如 `start_multi.cmd xiaoke`

## index-cli 正确用法

```cmd
cd C:\Users\24045\.openclaw\engine
set ENGINE_CONFIG=configs\xiaoke.json
npx tsx src\index-cli.ts --profile xiaoke --force
```

> 用 `configs/xiaoke.json` 而不是 `xiaoke-config.json`（后者只有memorySearch片断）

## DeepSeek Embedding Provider 修改

**文件**：`src/memory/shims/memory-core-host-engine-embeddings.ts`

已添加 deepseek adapter，autoSelectPriority 20（ollama是10）

## 遗留问题

- sqlite-vec unavailable：在 WSL/tsx 环境无法加载 Windows dll
- 需要在 Windows CMD 里跑才能用完整向量搜索
- 索引已成功（2 sources: memory + topics），走纯 CPU FTS 路径

## 待验证

- [ ] rebuild.cmd 后 dist/main-multi.js 生成
- [ ] 小柯新 profile 能否正常启动
- [ ] 向量搜索是否正常工作（在 Windows CMD 测试）
