---
name: cascade worker md_change_state upsert 重置机制
description: 2026-08-04 15:25 验证发现——cascade worker 的"放弃"状态存储在 md_change_state 表里，touch md 文件会触发 upsert 把 status 重置回 pending，retry_count 清零；这是绕过 OME worker 不自动重试的实操修复路径
type: reference
date: 2026-08-04
---

# cascade worker `md_change_state` 表的 upsert 重置机制

2026-08-04 15:25 我发现 episode 表 0 行的**最终修复突破**——cascade worker 的失败状态存储在 `md_change_state` 表里，touch 文件可以重置它。

## 背景

之前查到 cascade worker 失败不自动重试，episode 表就 0 行卡住。多次重启 EverOS 也没用。

## 最终修复姿势

1. 查 `md_change_state` 表发现两个 episode 状态：
   - `episode-2026-08-04.md`: status=processing（卡死）
   - `episode-2026-08-03.md`: status=failed, retryable=0, retry_count=12（永久失败）
2. 直接 `touch /root/.everos/topics/.../episode-2026-08-03.md` 和 08-04.md
3. mtime 变化 → `md_change_state` repo 的 upsert 触发 → status 重置回 `pending` + retry_count 清零
4. cascade worker 下次扫描检测到 pending → 重新入队 → 处理 → embedding → 写 lancedb

## 关键发现

- **touch 是万能 reset**：不管 worker 因为 processing 卡死还是 retry_count=12 永久放弃，touch 都能拉回 pending
- 之前推论"cascade 是 filesystem watcher，重启不重扫"是对的，但 touch 是**触发单个文件的 upsert**，不是整体重扫
- 验证修复成功：`SELECT status, retry_count FROM md_change_state` 应该看到 pending + 0

## 配套需要验证的事

- cascade 多久扫一次 md_change_state（可能是秒级/分钟级）
- ollama 跑得稳的时候，touch 完 episode embedding 才会真正生效
- touch 完 episode 表要有数据还要等几分钟到几十分钟（9s/embed × 几百次）

## Why

cascade worker 失败不自动重试 = 设计假设"embedding 服务永远可用"——但 ollama 会 OOM、远程 API 会超时。touch + md_change_state upsert 是这个设计缺口下的手动恢复路径。

## How to apply

- 诊断 "episode/cluster 表 0 行" 时：
  1. 先查 `md_change_state` 表看 status 是哪种
  2. 对 status=processing / status=failed 的文件全部 touch
  3. 等 cascade 重扫后查 episode 行数应该 > 0
- 注意 touch 不会修 embedding 服务——如果 ollama/DeepInfra 还挂，touch 完又会变成 failed，但 retry_count 从 0 开始有缓冲
- 配合 Docker VM 内存调大 → ollama 跑稳 → touch md → cascade 重处理 是完整修复链

## 关联

- @see reference_cascade_touch_md_重扫_不能只清lancedb_0804（同根因，更早发现的表象）
- @see reference_EverOS_OME_episode_extraction_0行根因（episode 0 行的三层根因）
- @see reference_EverOS_Docker_VM内存1.94G_bge-m3装不下_0804（VM 内存是关键前置条件）
- @see reference_EverOS_embedding_timeout30s边界死循环_0804（客户端 timeout 30s vs CPU 27s 的边界死循环，加成最后一层）

## ⚠️ 重要更新（2026-08-04 16:00）

touch 完 episode 进入 processing 后，**才算遇到最后一层根因**：everos.toml 里 `embedding.timeout = 30s`，CPU 跑大块 embedding 25-30s 经常被客户端掐断 → 疯狂 retry → episode 表永远不写入。
**正确顺序：先调 timeout 到 120s + 重启 EverOS，再 touch md**——否则 touch 完又会失败扣 retry_count。
详细见 @see reference_EverOS_embedding_timeout30s边界死循环_0804。
