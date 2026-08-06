# Spec: CogniFold 灌数据（batch import）

## 目标

把小柯和姐姐的 topics 记忆文件灌入 CogniFold，生成概念图谱，让翀哥能 query。

## 数据源

| 来源 | 路径 | 文件数 |
|------|------|--------|
| 小柯 topics | `/Users/chongzhang/xiaoke/workspace/topics/` | 278 |
| 姐姐 topics | `C:/Users/24045/.openclaw/workspace/topics/` | 1099 |
| 合计 | — | 1377 |

文件格式：`.md`，带 YAML frontmatter（name/description/type）。

## 运行环境

| 组件 | 配置 |
|------|------|
| LLM | dashscope-tp qwen3.7-plus（Token Plan 包月，OpenAI 兼容端点） |
| LLM endpoint | `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1` |
| LLM API key | `sk-sp-D.LIXRI.q0o5.MEQCIBFY0a4wa0lxOlAJ0fVsHtWWha32l3rdLPcngvmolLGbAiAS+NRj6iQ9VUXX8v5Mm/B2fvtMdkKeyRuPQAf9BPo91Q==` |
| Embedding | ollama bge-m3（本地） |
| Embedding endpoint | `http://localhost:11434/v1` |

## CogniFold 架构（灌数据相关）

CogniFold 灌数据分两步：

1. **build-timeline** — `wiki importer` 把 `.md` 文件解析成 `timeline.json`（chunk 切分 + frontmatter 解析）
2. **run** — `Pipeline` 逐条处理 timeline 里的 event，通过 LLM agent 提取概念 → 生成 `UpdatePlan` → 执行 plan → 更新概念图谱

### build-timeline（已有，不需重写）

CogniFold 自带 `cognifold.importers.wiki.build_wiki_timeline()`，支持：
- 递归扫描 `.md`/`.txt`/`.pdf`
- frontmatter 解析（YAML）
- heading/paragraph/fixed 三种 chunk 策略
- 输出 timeline.json

CLI: `python -m cognifold build-timeline --input <dir> --output <timeline.json>`

### run（需要适配）

Pipeline 初始化需要：
- `AgentConfig` — 设 `model_name="openai:qwen3.7-plus"`
- 环境变量 `OPENAI_API_KEY` + `OPENAI_BASE_URL` 指向 dashscope-tp Token Plan 端点
- Embedding — CogniFold 没有 ollama provider，需要加

### Embedding 问题

CogniFold `EmbeddingProviderType` 只有 GEMINI / OPENAI / MOCK。没有 ollama。

**方案：** OpenAIEmbeddingProvider 已经支持 `base_url`，ollama 也暴露 OpenAI 兼容端点（`http://localhost:11434/v1`）。用 `EmbeddingProviderType.OPENAI` + `base_url=http://localhost:11434/v1` + `model=bge-m3` 即可，不需要写新 provider。

需要改 `EmbeddingConfig` 支持 `base_url` 字段（当前 `extra_config` 里有但 `OpenAIEmbeddingProvider` 没读）。

## 要改的代码

### 1. EmbeddingConfig 加 base_url（`src/cognifold/embeddings/config.py`）

```python
@dataclass
class EmbeddingConfig:
    # ... 已有字段 ...
    base_url: str | None = None  # 新增：OpenAI 兼容端点（ollama/dashscope 等）
```

加一个 `for_ollama` classmethod：
```python
@classmethod
def for_ollama(cls, model: str = "bge-m3", base_url: str = "http://localhost:11434/v1"):
    return cls(
        provider=EmbeddingProviderType.OPENAI,
        model=model,
        dimensions=1024,  # bge-m3 默认 1024 维
        base_url=base_url,
        api_key="ollama",  # ollama 不需要 key 但 OpenAI client 要填
    )
```

### 2. OpenAIEmbeddingProvider 读 base_url（`src/cognifold/embeddings/providers.py`）

```python
# 在 __init__ 或 embed 时：
client = OpenAI(
    api_key=self.config.api_key or "unused",
    base_url=self.config.base_url,  # 新增
)
```

### 3. batch_import.py（新建，`scripts/batch_import.py`）

主脚本，串起 build-timeline → run → save graph：

```python
# 伪代码
1. 合并两个 topics 目录的文件列表
2. build_wiki_timeline(combined_dir) → timeline.json
3. 设环境变量 OPENAI_API_KEY + OPENAI_BASE_URL
4. config = CognifoldConfig(agent_model="openai:qwen3.7-plus", embedding=for_ollama())
5. pipeline = Pipeline(config)
6. pipeline.load_timeline(timeline.json)
7. 每 10 条 event 做一次 checkpoint（save graph + print 进度）
8. pipeline.run() → stats
9. pipeline.save_graph("output/full_graph.json")
```

**中断恢复：** checkpoint 保存已处理的 event index，重启时从上次 index 继续。

## 不改的代码

- `build_wiki_timeline()` — 已有，直接用
- `Pipeline` 核心逻辑 — 不改
- `ConceptGraph` — 不改
- `CognifoldAgent` — 不改（已有 `openai:` 前缀支持）

## 可验证目标（aim）

1. **1377 个 topics 全跑完不漏** — timeline.json events 数 >= topics 文件数
2. **full_graph.json 生成 + size > 1MB** — `output/full_graph.json` 存在且 `os.path.getsize > 1_000_000`
3. **测试 query 能召回相关概念** — 用 `cognifold query "翀哥"` 能返回相关节点

## 保护机制

- 每 10 条 event commit 一次 checkpoint（graph snapshot + event index）
- 中断后 `--resume` 从 checkpoint 继续
- 日志打印进度 `[batch_import] Processing 10/1377...`

## Karpathy 5 条红线自查

1. ❌ 假想"灵活性" → 没有。只做灌数据，不做 query UI、不做可视化
2. ❌ "如果以后要 X" → 没有。不预设其他数据源
3. ❌ 200 行能搞定不写 500 行 → batch_import.py 目标 < 150 行
4. ❌ 多种解释列出来 → embedding 用 OpenAI provider + ollama base_url（列了替代方案：写新 OllamaProvider，但不需要）
5. ❌ 不确定就问 → embedding dimensions 待确认（bge-m3 默认 1024 还是 768？需验证 ollama 实际返回维度）

## 风险

- **LLM 调用量大**：1377 个文件 × 平均 2-3 chunks = ~3500 events，每个 event 一次 LLM 调用。qwen3.7-plus RPM 限制 30 次/分钟，需限速
  - **方案：** batch_import.py 里每次 LLM 调用后 `time.sleep(2)`（= 30 次/分钟），或用 token bucket 节流
- **ollama 未装**：需要确认 ollama + bge-m3 model 已 pull
  - **验证方法：** 跑前先 `curl http://localhost:11434/v1/embeddings -d '{"model":"bge-m3","input":"test"}'`，看返回的 `data[0].embedding` 数组长度 = bge-m3 实际维度，写进 `for_ollama()` 的 `dimensions`
- **embedding dimensions 不匹配**：bge-m3 实际维度需验证，否则 search 会炸
  - **验证方法：** 同上 curl，返回维度写入 config，不用猜

## 文件清单

| 文件 | 动作 | 说明 |
|------|------|------|
| `src/cognifold/embeddings/config.py` | 改 | 加 `base_url` 字段 + `for_ollama` |
| `src/cognifold/embeddings/providers.py` | 改 | `OpenAIEmbeddingProvider` 读 `base_url` |
| `scripts/batch_import.py` | 新建 | 主脚本 |
| `output/full_graph.json` | 生成 | 最终产出 |

## 环境验证（跑之前必须做）

```bash
# 1. 确认 ollama + bge-m3 已装
curl http://localhost:11434/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"bge-m3","input":"test"}'
# → 看 data[0].embedding 数组长度，写入 for_ollama() 的 dimensions

# 2. 确认 Token Plan 端点可用
curl https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer sk-sp-D.LIXRI..." \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.7-plus","messages":[{"role":"user","content":"hi"}]}'
# → 200 + 有回复 = 端点可用
```
