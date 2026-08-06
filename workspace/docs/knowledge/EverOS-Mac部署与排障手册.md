# EverOS Mac 部署与排障手册

> 8/4 细化落盘。Mac（无 GPU）+ Docker 容器跑 EverOS 全栈：EverOS 主服务 + agentic search + ollama bge-m3。
> 参考：`workspace/research/EverOS/`（submodule，上游 HEAD）、部署文件备份在 `/Users/chongzhang/work/everos-deploy/`（不进 git）。
> 翀哥要求：**不用 OME 策略，不省步骤，姐姐那边验证过的流程为准。**

---

## 1. 架构

```
Mac 宿主机（16GB，无 GPU）
└── Docker VM（必须 ≥8GB 内存，默认 2GB 必炸）
    └── everos 容器
        ├── ollama serve (127.0.0.1:11434)      ← bge-m3 embedding，CPU 跑
        ├── everos server (0.0.0.0:8100)         ← memorize/flush/search 主 API
        └── agentic_server (0.0.0.0:8101)        ← engine memory_search 走的入口

数据流：
topics/*.md ──import 脚本──> /api/v1/memory/add ──> memcell(sqlite)
        ──flush──> boundary 检测 ──> episode extraction ──> episode md + lancedb 索引
search: /api/v1/memory/search = dense(ollama bge-m3) + sparse(BM25) RRF → rerank(DeepInfra)
```

**三个 lancedb 表缺一不可**（"数据存在"要三层全验证）：
1. 磁盘 episode md 文件（`/root/.everos/xiaoke/default_project/users/xiaoke/episodes/`）
2. sqlite `system.db` 的 memcell 表
3. lancedb `episode.lance` 表 ← search 真正查的是这个

## 2. Docker 资源配置（8/4 事故第一根因）

`~/Library/Group Containers/group.com.docker/settings.json`：

```json
"memoryMiB": 8192,   // 默认 2048！bge-m3 要 ~1.16GB + 1GB free target，2GB 必 OOM
"swapMiB": 2048
```

改完必须**彻底重启 Docker Desktop**（osascript quit 不干净，要 `killall` 整条进程链：Docker / com.docker.supervisor / com.docker.backend / com.docker.hyperkit，vmnetd 是系统特权不用杀），再 `open -a Docker`。验证：`docker info | grep "Total Memory"` 应 ≥7.7GiB。

**OOM 症状**（ollama_serve.log）：
```
llama-server process no longer running ... signal: killed
cannot meet free memory target of 1024 MiB ... abort
```
小文件（atomic_fact/foresight）能过、大文件（episode）必挂 = 内存不够的典型特征。

## 3. 容器参数

**Mounts：**
| 宿主机 | 容器 | 说明 |
|--------|------|------|
| docker volume `everos-data` | `/root/.everos` | 全部持久数据（sqlite + lancedb + episode md） |
| `/Users/chongzhang/xiaoke/workspace/topics` | `/root/.everos/topics` | import 脚本的 topics 源（bind） |

**Env（关键，其余见 topics/reference/ref_proxy配置… 旁的容器 inspect）：**
```
EVEROS_LLM__MODEL=MiniMax-M3
EVEROS_LLM__API_KEY=<MiniMax key>
EVEROS_LLM__BASE_URL=https://api.minimaxi.com/v1
EVEROS_EMBEDDING__MODEL=bge-m3                 # 必须本地 ollama，不花钱
EVEROS_EMBEDDING__API_KEY=ollama
EVEROS_EMBEDDING__BASE_URL=http://127.0.0.1:11434/v1
EVEROS_RERANK__MODEL=Qwen/Qwen3-Reranker-4B    # rerank 走 DeepInfra（要 key）
EVEROS_RERANK__API_KEY=<deepinfra key>
EVEROS_RERANK__BASE_URL=https://api.deepinfra.com/v1/inference
EVEROS_ROOT=/root/.everos
TZ=Asia/Shanghai
```

**everos.toml 两个必改项（改完重启容器才生效）：**
- `[embedding] base_url` → 本地 ollama（默认出厂是 DeepInfra + 空 key，search 必超时）
- `[embedding] timeout_seconds = 120`（默认 30！CPU 上 bge-m3 单块 5-30s，30s 必踩边界超时→重试死循环）

**ome.toml：三个策略保持 `enabled = false`**（extract_foresight / extract_atomic_facts / extract_agent_case）——翀哥 8/4 拍板不用 OME。

## 4. 数据导入（不省步骤）

用容器内 `/tmp/import_everos_mac.py`（源在 research/EverOS 目录）：
- 走标准管线 `/api/v1/memory/add`，`MAX_CONCURRENCY=1`，`MAX_RETRIES=0`，断点续跑 `--resume`
- 进度文件 `/tmp/import_progress.json`
- **注意**：脚本里 flush 被 skip（"add-only mode"）。add 只写 memcell/unprocessed_buffer；**episode extraction 靠 flush 或 cascade watcher 触发**，别以为 add 完就等于灌完。

## 5. 8/4 事故根因清单（按发现顺序，全部踩过）

| # | 根因 | 症状 | 修复 |
|---|------|------|------|
| 1 | embedding 出厂指 DeepInfra 空 key | search 60s 超时 | env 指 ollama bge-m3 |
| 2 | import 脚本 skip flush | 813 memcell 进 buffer，episode 不提取 | 手动 flush 或靠 cascade |
| 3 | **Docker VM 2GB 内存** | ollama OOM kill，episode 永久 failed(retry_count=12) | memoryMiB 8192 + 彻底重启 |
| 4 | md_change_state 卡 failed/processing 不自动重试 | episode md 在盘上但 lancedb 0 行 | `touch` episode md → upsert 重置 status 回 pending、retry_count 清零 |
| 5 | embedding timeout 30s 撞 CPU 耗时边界 | 反复 "Retrying request to /embeddings" | timeout_seconds 120 |

**判断"正常慢 vs 又卡住"三件套**：ollama 日志（有 200 且在跑）+ md_change_state status（processing 而非 failed/stuck）+ episode.lance 行数。CPU bge-m3 单块 5-20s，822KB episode 全量 2-4 小时，属正常慢。

**search 端点**：`POST /api/v1/memory/search`（不是 /api/search / /recall 那些，全 404）。engine 侧实现在 `src/memory/memdir/findRelevantMemoriesEveros.ts`。

## 6. 日常运维

```bash
docker restart everos                     # 重启三服务（start.sh 拉起 ollama+everos+agentic）
docker logs everos --tail 20              # 主日志
docker exec everos tail -20 /tmp/ollama_serve.log   # ollama/嵌入日志
docker stats everos --no-stream           # 内存水位（应 <7.8G 上限的 ~40%）

# 检查处理进度
docker exec everos python3 -c "
import lancedb; db=lancedb.connect('/root/.everos/.index/lancedb')
print('episode:', db.open_table('episode').count_rows())"
```

**磁盘**：Mac 磁盘常 90%+，Docker.raw 是大头；可清 build cache（`docker builder prune -af`）、悬空镜像、Downloads 大文件（先问翀哥）。

## 7. 待办

- [ ] episode 全量索引完成后端到端测 search（unlock 8/4 17:30）
- [ ] Grok/my_selfie 走代理问题与 EverOS 无关，但 Mac 上 x.ai 直连不通，engine 启动需 `HTTP_PROXY=127.0.0.1:33210`（见 ref_proxy 配置文档）

## 相关文档

- [topics/reference/ref_proxy配置_grok和engine重启_0804.md](../../topics/reference/ref_proxy配置_grok和engine重启_0804.md)
- [topics/reference/reference_EverOS_OME_episode_extraction_0行根因.md](../../topics/reference/reference_EverOS_OME_episode_extraction_0行根因.md)
- [topics/reference/reference_cascade_CPU_embedding速度预期_0804.md](../../topics/reference/reference_cascade_CPU_embedding速度预期_0804.md)
