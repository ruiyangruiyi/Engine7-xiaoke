# 向量数据库架构笔记 (6/6)

## 三层架构

```
Memory Sources → Embedding Provider → Vector Store
```

### 1. Memory Sources（数据源）

- `memory/` — MEMORY.md + memory/ 目录
- `sessions/` — agents/*/sessions/*.jsonl
- `extraPaths` — 自定义目录（如 topics/, docs/）

配置：`agents.defaults.memorySearch.sources` + `extraPaths`

### 2. Embedding Provider（向量生成）

| Provider ID | 类型 | 说明 |
|-------------|------|------|
| `ollama` | 本地 | 需要 Ollama 服务运行 + bge-m3 模型 |
| `local` | 本地 | node-llama-cpp，需 GGUF 模型文件 |
| `remote` | 远程 | OpenAI 兼容格式（DeepSeek 等） |

**Ollama 配置示例**：
```bash
ollama pull bge-m3
# 模型名：nomic-embed-text 或 bge-m3
```

**远程 API 配置**（DeepSeek 为例）：
```json
{
  "provider": "deepseek-remote",
  "model": "deepseek-v4-pro",
  "remote": {
    "baseUrl": "https://api.deepseek.com/v1",
    "apiKey": "YOUR_KEY"
  }
}
```

### 3. Vector Store（向量存储）

**引擎**：sqlite-vec（SQLite 向量扩展）

**扩展路径**：
- Windows: `node_modules/sqlite-vec-windows-x64/vec0.dll`
- Linux: `node_modules/sqlite-vec-linux-x64/vec0.so`
- Mac ARM: `node_modules/sqlite-vec-darwin-arm64/vec0.dylib`

**加载方式**：
```typescript
import { loadSqliteVecExtension } from './memory/host/sqlite-vec.js'
const result = await loadSqliteVecExtension({ db, extensionPath: '...' })
```

## Engine 配置结构

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "provider": "ollama",
        "model": "bge-m3",
        "sources": ["memory", "sessions"],
        "extraPaths": ["docs"],
        "store": {
          "vector": {
            "extensionPath": "C:\\Users\\24045\\.openclaw\\engine\\node_modules\\sqlite-vec-windows-x64\\vec0.dll"
          }
        }
      }
    }
  }
}
```

## 关键源码文件

- `src/memory/host/sqlite-vec.ts` — sqlite-vec 扩展加载
- `src/memory/host/embeddings.ts` — local provider（node-llama-cpp）
- `src/memory/host/embeddings-remote-provider.ts` — 远程 API provider
- `src/memory/host/embeddings-remote-client.ts` — 远程客户端（Bearer token）
- `src/memory/host/backend-config.ts` — 完整配置解析（含 QMD 支持）
- `src/memory/host/internal.ts` — 文件扫描 + 分块逻辑

## 验证方法

启动后检查日志：
```
[memory] Vector store initialized with sqlite-vec
[memory] Embedding provider: ollama (bge-m3)
[memory] Indexed sources: memory, sessions, docs
```

## 小柯新 Profile 的向量配置

小柯新 Engine profile (`D:\xiaoke`) 可以复用已有的 `deepseek` provider：

```json
{
  "id": "xiaoke",
  "memorySearch": {
    "enabled": true,
    "provider": "deepseek",
    "model": "deepseek-v4-pro",
    "sources": ["memory", "topics"]
  }
}
```

需确保 `stateDir` 下有 `memory/` 目录，topics 已在 `D:/xiaoke/topics/`。
