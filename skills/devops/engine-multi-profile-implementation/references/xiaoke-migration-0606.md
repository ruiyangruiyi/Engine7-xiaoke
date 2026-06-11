# 小柯 Migration 进度 (6/6)

## 记忆文件位置

**实际路径**：`/mnt/wslg/distro/home/chong/D:/xiaoke/`

包含：MEMORY.md (7416字节)、SOUL.md (2202字节)、USER.md (3640字节)、topics/ (19个文件)、skills/ (28个文件)

## xiaoke profile 配置

**独立配置**：`/mnt/c/Users/24045/.openclaw/engine/xiaoke-config.json`
```json
{
  "_comment": "小柯(xiaoke) profile 向量索引专用配置",
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "sources": ["memory", "topics"],
        "extraPaths": ["/mnt/wslg/distro/home/chong/D:/xiaoke/topics"],
        "store": {
          "vector": {
            "extensionPath": "C:\\Users\\24045\\.openclaw\\engine\\node_modules\\sqlite-vec-windows-x64\\vec0.dll"
          }
        }
      }
    }
  },
  "models": {
    "providers": {
      "deepseek": {
        "baseUrl": "https://api.deepseek.com/anthropic",
        "apiKey": "sk-e3c...5bf4",
        "api": "anthropic"
      }
    }
  }
}
```

**engine-config.json 已修改**：xiaoke profile 的 extraPaths 改为 `/mnt/wslg/distro/home/chong/D:/xiaoke/topics`

## DeepSeek Embedding Provider 修改

**文件**：`/mnt/c/Users/24045/.openclaw/engine/src/memory/shims/memory-core-host-engine-embeddings.ts`

已添加 deepseek adapter，autoSelectPriority 20（ollama 是 10）

## index-cli 新参数

```bash
cd engine && npx tsx src/index-cli.ts --config xiaoke-config.json --profile xiaoke --force
```

## 遗留问题

- sqlite-vec unavailable：在 WSL/tsx 环境无法加载 Windows dll
- 需要在 Windows CMD 里跑才能用向量搜索
- 索引已成功（2 sources: memory + topics），但走的是纯 CPU FTS 路径

## 待验证

- [ ] 小柯新 profile 能否正常启动
- [ ] 向量搜索是否正常工作（在 Windows CMD 测试）
