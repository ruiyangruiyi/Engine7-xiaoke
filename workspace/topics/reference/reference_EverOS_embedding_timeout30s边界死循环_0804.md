---
name: EverOS embedding 客户端 30s timeout 在大块 CPU bge-m3 下边界死循环
description: 2026-08-04 15:30 排查 episode 持续 0 行找到的最后一层根因——EverOS embedding 客户端超时默认 30s，CPU 跑 822KB 大块要 27s 刚好逼近 30s，被掐断后疯狂 retry/retry/retry；调到 120s 后 episode 才进入正常 processing 轨道（pending→processing, retry=0, 24s/块）
type: reference
date: 2026-08-04
---

# EverOS embedding 客户端 30s timeout 边界死循环（最后一层根因）

2026-08-04 15:30 episode 处理反复失败的**最后一层根因**——前面 Docker VM 内存调到 8GB、bge-m3 跑稳、touch md 触发 cascade 重置都做了，但 episode 还是 0 行。挖到 everos.toml 的 `embedding.timeout = 30s` 才彻底破案。

## 根因链

```
CPU bge-m3 跑 822KB episode 大块 embedding：5-30s/块（中位数 27s）
EverOS embedding 客户端超时：30s
→ 27s 的请求有 30% 卡在 30.0007s 被掐断（400 = client timeout）
→ 触发 httpx retry
→ 重试再超时 → 再重试 → 死循环
→ cascade worker 看到的全是 `Retrying request to /embeddings`
→ episode 表永远不写入
```

OLLAMA CPU 跑 27s/块已经到顶，客户端 30s 没给任何缓冲。

## 关键日志对比

**修之前**（30s timeout）：
```
Retrying request to /embeddings
400 at 30.0007s  ← 用户级 timeout
```
ollama 侧 `[GIN] POST /v1/embeddings 200` 早就成功了，但 EverOS 客户端已经掐断重试了——典型的「服务端成功但客户端被自己 timeout」。

**修之后**（120s timeout）：
```
md_change_state: pending → processing  ✅
retry_count: 0  ← 不再疯狂重试
embedding: 24s/块  ← 稳定跑完
```

## 实战修复

```bash
# everos.toml 或 ome.toml 里
embedding.timeout = 120  # 从 30 调到 120
```

⚠️ **timeout 字段要重启 EverOS 才生效**——不是热加载。重启容器后 sqlite 的 md_change_state 状态保留，cascade 会自动扫描 pending 的文件继续处理。

## 跟之前几层根因的关系

不是互相替代，是**层层叠加**：
1. **Docker VM 1.94GB** → bge-m3 OOM kill（@see reference_EverOS_Docker_VM内存1.94G_bge-m3装不下_0804）
2. **默认 embedding 配 DeepInfra + 空 key** → dense_recall/OME 调远程永远超时（@see reference_EverOS_embedding配置默认DeepInfra_不是ollama）
3. **cascade worker 遇 EmbeddingServiceError 不重试 + 失败的 md 不重扫**（@see reference_cascade_md_change_state_upsert机制_0804）
4. **embedding 客户端 30s timeout vs CPU 大块 27s** ← 这一层

**只有 Docker 内存和 embedding 配置修了**，episode 才会进入**正常 processing** 轨道。但**再没修 timeout**，处理也会卡在「请求边界超时 → 疯狂重试 → episode 表永远 0」。

## Why

CPU embedding 性能上有个事实：跑大块（>500KB / 高 token 数）时单次 inference 在 25-30s 是常态，特别是 bge-m3 长上下文。客户端 timeout 拍脑袋写 30s 看起来「够」但实际是卡在边界。

## How to apply

- **EverOS/CPU ollama embedding 必须 timeout ≥ 120s**——30s 在大文件下必然卡边界
- `everos.toml` 改了 timeout 字段后**别指望热加载**——重启容器
- 重启 EverOS 时 md_change_state 状态会保留，cascade 会自动重扫 pending，不用手动 touch
- episode 表「长时间 0 行」要查三层活跃度：
  - ollama 日志有新 embedding 请求
  - task_id 持续推进
  - md_change_state 是 processing 不是 failed
- 看到 `Retrying request to /embeddings` + `400 at 30.0007s` → 100% 是 timeout 不够大，不是 ollama 崩
- 大文件预期：~400-800 次 embedding × 24s = 2-3 小时（@see reference_cascade_CPU_embedding速度预期_0804）

## 完整修复链（最终版）

1. Docker VM 内存 → 8GB（pkill + launchctl 拉起）
2. 确认本地 ollama bge-m3 在跑（`curl http://localhost:11434/api/tags`）
3. everos.toml `embedding.timeout` → 120s
4. 重启 EverOS 容器
5. cascade 会自动扫描 pending episode md → 进入正常 processing
6. 等 2-3 小时 episode 表行数 > 0 → memory_search 才真正能返回
