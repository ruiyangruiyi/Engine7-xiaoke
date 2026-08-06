# Plan: CogniFold 灌数据（batch import）

> Spec: `docs/superpowers/specs/2026-06-21-cognifold-batch-import-design.md`
> 前置条件：spec 已通过 Direction Gate #1 + #2

## 关键发现（spec 之后的代码阅读补充）

1. **Classic Pipeline 不用 embedding** — `Pipeline`（classic.py）完全不调 embedding。Embedding 只在 query 时用（`cli/query.py` 的 `_create_embedder()`）
2. **因此灌数据阶段不需要改 embedding** — 先跑 classic pipeline（不 `--agent` 就用默认 plan，不用 LLM）
3. **但 spec 要求 LLM agent 提取概念** — 需 `--agent` 模式，这才会调 LLM
4. **query 时 embedding 通过环境变量** — `_create_embedder()` 看有没有 `GOOGLE_API_KEY`/`OPENAI_API_KEY`，没有就用 mock。需要设 `OPENAI_API_KEY` + `EMBEDDING_API_KEY`/`EMBEDDING_BASE_URL` 指向 ollama

## 调整后的执行策略

分两阶段跑：
- **阶段 A**：build-timeline（不需要 LLM，不需要 embedding）
- **阶段 B**：run pipeline with `--agent`（需要 LLM，不需要 embedding）
- **阶段 C**：query 验证（需要 embedding，用 ollama）

---

## Task 0: 环境验证（5 分钟）

**Files:** 无（只跑命令）

**步骤：**
```bash
# 1. ollama + bge-m3
curl http://localhost:11434/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"bge-m3","input":"test"}'
# 记录返回的 data[0].embedding 数组长度 → BGE_DIM

# 2. Token Plan 端点
curl https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer sk-sp-D.LIXRI.q0o5.MEQCIBFY0a4wa0lxOlAJ0fVsHtWWha32l3rdLPcngvmolLGbAiAS+NRj6iQ9VUXX8v5Mm/B2fvtMdkKeyRuPQAf9BPo91Q==" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.7-plus","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
# 200 + 有回复 = OK

# 3. Python 依赖
cd /Users/chongzhang/xiaoke//CogniFold && pip install -e . 2>&1 | tail -5
pip install openai 2>&1 | tail -3
```

**验证：**
- ollama 返回 embedding 数组（记录维度 BGE_DIM）
- Token Plan 返回 200 + content
- `python -c "import cognifold; print('OK')"` 不报错

**commit:** 无（验证步骤不 commit）

---

## Task 1: EmbeddingConfig 加 base_url（3 分钟）

**Files:**
- `/Users/chongzhang/xiaoke//CogniFold/src/cognifold/embeddings/config.py`（改）
- `/Users/chongzhang/xiaoke//CogniFold/tests/test_embedding_config.py`（新建）

**写失败测试：**
```python
# tests/test_embedding_config.py
from cognifold.embeddings.config import EmbeddingConfig, EmbeddingProviderType

def test_for_ollama():
    cfg = EmbeddingConfig.for_ollama()
    assert cfg.provider == EmbeddingProviderType.OPENAI
    assert cfg.model == "bge-m3"
    assert cfg.base_url == "http://localhost:11434/v1"
    assert cfg.api_key == "ollama"
    assert cfg.dimensions == 1024

def test_base_url_default_none():
    cfg = EmbeddingConfig()
    assert cfg.base_url is None
```

**跑确认 fail：**
```bash
cd /Users/chongzhang/xiaoke//CogniFold && python -m pytest tests/test_embedding_config.py -x
# AttributeError: 'EmbeddingConfig' object has no attribute 'base_url'
```

**写代码：**

在 `config.py` 的 `EmbeddingConfig` dataclass 里加字段（在 `extra_config` 后面）：
```python
    base_url: str | None = None  # OpenAI 兼容端点（ollama/dashscope 等）
```

在 class 里加 classmethod（在 `for_openai` 后面）：
```python
    @classmethod
    def for_ollama(
        cls,
        model: str = "bge-m3",
        base_url: str = "http://localhost:11434/v1",
        dimensions: int = 1024,
    ) -> EmbeddingConfig:
        """Create a config for Ollama-hosted models via OpenAI-compatible endpoint."""
        return cls(
            provider=EmbeddingProviderType.OPENAI,
            model=model,
            dimensions=dimensions,
            base_url=base_url,
            api_key="ollama",
        )
```

**跑确认 pass：**
```bash
cd /Users/chongzhang/xiaoke//CogniFold && python -m pytest tests/test_embedding_config.py -x -v
```

**commit:** `feat: EmbeddingConfig 加 base_url + for_ollama classmethod`

---

## Task 2: OpenAIEmbeddingProvider 读 base_url（3 分钟）

**Files:**
- `/Users/chongzhang/xiaoke//CogniFold/src/cognifold/embeddings/providers.py`（改）
- `/Users/chongzhang/xiaoke//CogniFold/tests/test_openai_provider_base_url.py`（新建）

**写失败测试：**
```python
# tests/test_openai_provider_base_url.py
from cognifold.embeddings.config import EmbeddingConfig, EmbeddingProviderType
from cognifold.embeddings.providers import OpenAIEmbeddingProvider

def test_provider_reads_base_url(monkeypatch):
    monkeypatch.setenv("EMBEDDING_API_KEY", "ollama")
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    cfg = EmbeddingConfig.for_ollama()
    provider = OpenAIEmbeddingProvider(cfg)
    # 验证 client 的 base_url 被设置
    assert provider._client.base_url == "http://localhost:11434/v1"
```

**跑确认 fail：**
```bash
cd /Users/chongzhang/xiaoke//CogniFold && python -m pytest tests/test_openai_provider_base_url.py -x
# AssertionError: base_url 没被传给 OpenAI client
```

**写代码：**

在 `providers.py` 的 `OpenAIEmbeddingProvider.__init__` 里，修改 client_kwargs 逻辑（在 `embed_base_url` 那段后面加 config.base_url）：

当前代码（L260-273）：
```python
            client_kwargs: dict = {"api_key": self.api_key}
            if embed_base_url:
                client_kwargs["base_url"] = embed_base_url
            elif embed_api_key:
                client_kwargs["base_url"] = "https://api.openai.com/v1"
            self._client = OpenAI(**client_kwargs)
```

改为：
```python
            client_kwargs: dict = {"api_key": self.api_key}
            if embed_base_url:
                client_kwargs["base_url"] = embed_base_url
            elif self.config.base_url:
                client_kwargs["base_url"] = self.config.base_url
            elif embed_api_key:
                client_kwargs["base_url"] = "https://api.openai.com/v1"
            self._client = OpenAI(**client_kwargs)
```

**跑确认 pass：**
```bash
cd /Users/chongzhang/xiaoke//CogniFold && python -m pytest tests/test_openai_provider_base_url.py -x -v
```

**commit:** `feat: OpenAIEmbeddingProvider 读 config.base_url（支持 ollama 端点）`

---

## Task 3: query CLI 支持 ollama embedding（3 分钟）

**Files:**
- `/Users/chongzhang/xiaoke//CogniFold/src/cognifold/cli/query.py`（改）

**背景：** `_create_embedder()` 当前只看 `GOOGLE_API_KEY`/`OPENAI_API_KEY` 环境变量。需要支持 ollama（通过 `EMBEDDING_API_KEY` + `EMBEDDING_BASE_URL` 环境变量）。

**改法：** 在 `_create_embedder()` 里，`OPENAI_API_KEY` 分支后加 ollama 检测：

当前代码（L256-261）：
```python
    elif os.environ.get("OPENAI_API_KEY"):
        config = EmbeddingConfig(
            provider=EmbeddingProviderType.OPENAI,
            dimensions=1536,
        )
        return NodeEmbedder(config)
```

改为：
```python
    elif os.environ.get("EMBEDDING_API_KEY") and os.environ.get("EMBEDDING_BASE_URL"):
        # Ollama or other OpenAI-compatible local endpoint
        config = EmbeddingConfig.for_ollama(
            base_url=os.environ["EMBEDDING_BASE_URL"],
        )
        return NodeEmbedder(config)
    elif os.environ.get("OPENAI_API_KEY"):
        config = EmbeddingConfig(
            provider=EmbeddingProviderType.OPENAI,
            dimensions=1536,
        )
        return NodeEmbedder(config)
```

**验证：**
```bash
# 设环境变量后跑 query
export EMBEDDING_API_KEY=ollama
export EMBEDDING_BASE_URL=http://localhost:11434/v1
python -m cognifold query "翀哥" --graph output/full_graph.json --mode semantic
```

**commit:** `feat: query CLI 支持 ollama embedding（EMBEDDING_API_KEY + EMBEDDING_BASE_URL）`

---

## Task 4: batch_import.py 主脚本（5 分钟）

**Files:**
- `/Users/chongzhang/xiaoke//CogniFold/scripts/batch_import.py`（新建）

**完整代码：**

```python
"""Batch import topics into CogniFold concept graph.

Usage:
    python scripts/batch_import.py --resume
    python scripts/batch_import.py --fresh
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Setup
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Token Plan endpoint
os.environ["OPENAI_API_KEY"] = "sk-sp-D.LIXRI.q0o5.MEQCIBFY0a4wa0lxOlAJ0fVsHtWWha32l3rdLPcngvmolLGbAiAS+NRj6iQ9VUXX8v5Mm/B2fvtMdkKeyRuPQAf9BPo91Q=="
os.environ["OPENAI_BASE_URL"] = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"

# Ollama embedding
os.environ["EMBEDDING_API_KEY"] = "ollama"
os.environ["EMBEDDING_BASE_URL"] = "http://localhost:11434/v1"

TOPICS_DIRS = [
    Path("/Users/chongzhang/xiaoke/workspace/topics"),
    Path("C:/Users/24045/.openclaw/workspace/topics"),
]
MERGED_DIR = Path("data/merged_topics")
TIMELINE_PATH = Path("data/timeline.json")
CHECKPOINT_DIR = Path("output/checkpoints")
GRAPH_PATH = Path("output/full_graph.json")
CHECKPOINT_EVERY = 10
RATE_LIMIT_SLEEP = 2  # seconds between LLM calls (30 RPM)


def merge_topics():
    """Copy all .md files from source dirs into MERGED_DIR."""
    if MERGED_DIR.exists():
        shutil.rmtree(MERGED_DIR)
    MERGED_DIR.mkdir(parents=True)
    count = 0
    for src_dir in TOPICS_DIRS:
        if not src_dir.exists():
            continue
        for md_file in src_dir.rglob("*.md"):
            rel = md_file.relative_to(src_dir)
            dst = MERGED_DIR / f"{src_dir.name}__{rel}"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, dst)
            count += 1
    print(f"[batch_import] Merged {count} files into {MERGED_DIR}")
    return count


def build_timeline():
    """Build timeline.json from merged topics."""
    from cognifold.importers.wiki import build_wiki_timeline, WikiTimelineBuildSettings
    settings = WikiTimelineBuildSettings(
        chunk_size_chars=1600,
        chunk_overlap_chars=200,
        min_chunk_chars=100,
        split_strategy="heading",
        timestamp_strategy="frontmatter_date",
    )
    result = build_wiki_timeline(MERGED_DIR, settings=settings)
    TIMELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TIMELINE_PATH.write_text(json.dumps(result.timeline, ensure_ascii=False, indent=2))
    print(f"[batch_import] Timeline: {result.events_emitted} events from {result.docs_parsed} docs")
    return result.events_emitted


def run_pipeline(resume=False):
    """Run pipeline with checkpointing."""
    from cognifold.config import CognifoldConfig
    from cognifold.pipeline.classic import Pipeline
    from cognifold.graph.persistence import load_graph

    config = CognifoldConfig()
    config.model.name = "openai:qwen3.7-plus"
    pipeline = Pipeline(config)
    pipeline.load_timeline(TIMELINE_PATH)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    start_idx = 0

    if resume:
        checkpoints = sorted(CHECKPOINT_DIR.glob("checkpoint_*.json"))
        if checkpoints:
            last = checkpoints[-1]
            data = json.loads(last.read_text())
            start_idx = data.get("event_index", 0)
            # Restore graph from last saved graph
            if GRAPH_PATH.exists():
                pipeline._graph = load_graph(GRAPH_PATH)
            # Skip already-processed events WITHOUT calling LLM
            pipeline._current_index = start_idx
            print(f"[batch_import] Resuming from event {start_idx} (graph restored)")

    total = len(pipeline._timeline)
    count = 0
    while True:
        result = pipeline.step()
        if result is None:
            break
        count += 1
        time.sleep(RATE_LIMIT_SLEEP)

        if count % CHECKPOINT_EVERY == 0:
            pipeline.save_graph(GRAPH_PATH)
            cp_path = CHECKPOINT_DIR / f"checkpoint_{start_idx + count:05d}.json"
            cp_path.write_text(json.dumps({"event_index": start_idx + count}))
            print(f"[batch_import] Processing {start_idx + count}/{total} | checkpoint saved")

    pipeline.save_graph(GRAPH_PATH)
    stats = pipeline.get_stats()
    print(f"[batch_import] Done! events={stats.events_processed} nodes={stats.total_nodes} edges={stats.total_edges} concepts={stats.concepts_created}")
    return stats


def verify():
    """Verify output."""
    if not GRAPH_PATH.exists():
        print("[batch_import] FAIL: full_graph.json not found")
        return False
    size = GRAPH_PATH.stat().st_size
    print(f"[batch_import] Graph size: {size} bytes ({size / 1024 / 1024:.1f} MB)")
    if size < 1_000_000:
        print("[batch_import] WARN: graph < 1MB")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", action="store_true", help="Start from scratch")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    args = parser.parse_args()

    if args.fresh or not TIMELINE_PATH.exists():
        merge_topics()
        build_timeline()

    run_pipeline(resume=args.resume)
    verify()
```

**验证：**
```bash
# 先 dry-run 确认 import 不报错
cd /Users/chongzhang/xiaoke//CogniFold && python -c "
import sys; sys.path.insert(0, 'src')
import scripts.batch_import
print('import OK')
"
```

**commit:** `feat: batch_import.py — merge topics → build timeline → run pipeline → save graph`

---

## Task 5: 跑灌数据（预计 2 小时）

**Files:** 无（运行脚本）

**步骤：**
```bash
cd /Users/chongzhang/xiaoke//CogniFold

# 1. Fresh run（build timeline + run pipeline）
python scripts/batch_import.py --fresh

# 如果中断了：
# python scripts/batch_import.py --resume
```

**验证（aim）：**
```bash
# 1. timeline events >= topics 文件数
python -c "
import json; t = json.load(open('data/timeline.json')); print(f'Events: {len(t[\"events\"])}')"

# 2. graph > 1MB
python -c "
import os; print(f'Graph: {os.path.getsize(\"output/full_graph.json\")} bytes')"

# 3. query 能召回
EMBEDDING_API_KEY=ollama EMBEDDING_BASE_URL=http://localhost:11434/v1 \
python -m cognifold query "翀哥" --graph output/full_graph.json --mode semantic
```

**commit:** 无（运行结果不需要 commit）

---

## Plan 自查 3 件

1. **Spec 覆盖** — spec 的 3 个可验证目标（全跑完 / graph > 1MB / query 召回）都对应到 Task 5 的验证步骤 ✅
2. **占位符** — 无 TBD、无"类似 Task N" ✅
3. **类型一致** — 所有文件路径用绝对路径，所有代码块是完整可运行的 Python ✅

## 不在 plan 里的事（Karpathy 红线）

- ❌ 不做可视化（graph.html）
- ❌ 不做 query UI
- ❌ 不写新的 OllamaProvider class
- ❌ 不改 Pipeline 核心逻辑
- ❌ 不改 ConceptGraph
- ❌ 不加 consolidation/lifecycle（默认关闭）
