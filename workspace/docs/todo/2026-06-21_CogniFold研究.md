# CogniFold 研究 + 跑通

**来源：** 翀哥 6/21 00:32 看到 Reddit 帖子 → 让我研究
**优先级：** 高（翀哥说"明天跑起来"）

## 背景
翀哥在 Reddit 看到一个帖子，介绍 OpenNorve 公司做的 **CogniFold** 项目——
"Always-On Proactive Memory via Cognitive Folding"，是给 agent 装"前额叶"的开源实现。

核心一句话：
> **主动性不是 agent 自己想出来的，是事件累积形成拓扑结构，意图从结构里自己涌现。**

## 已完成
- [x] 找到正确 repo（翀哥拼错过：OpenNerve ❌ → OpenNorve ✅）
- [x] Clone 到 `/Users/chongzhang/xiaoke//CogniFold/`
- [x] 看了 README 核心概念

## 待办
### 阶段 1：理解架构
- [ ] 读 `cognifold/` 源码，看四种节点（event/concept/intent/time）怎么实现
- [ ] 读 `docs/ARCHITECTURE.md`（README 里提到的）
- [ ] 看概念聚类算法（concept 怎么从 event 抽象出来）
- [ ] 看 intent 触发条件（"concept 簇密度达标"具体怎么算）
- [ ] 看八种 typed edges 怎么定义

### 阶段 2：跑通
- [ ] 看 `pyproject.toml` 装依赖
- [ ] 跑 README 里的 quick start
- [ ] 看 live demo（https://opennorve.github.io/CogniFold/）
- [ ] 跑 CogEval-Bench（README 提到的 benchmark）

### 阶段 3：跟翀哥现有体系对比
- [ ] 跟五层记忆 L0-L3 对照表
- [ ] 看 Intent 触发器能不能移植到 OpenClaw
- [ ] 看 typed edges 能不能丰富 OpenClaw 的双向链接
- [ ] 写一份"启发清单"——哪些思路能借鉴，哪些要保留"养"的核心

### 阶段 4：试点集成（待翀哥决定）
- [ ] 跟翀哥汇报研究结果
- [ ] 决定要不要借鉴到 OpenClaw
- [ ] 决定要不要加到小柯的 recall 机制里

## 核心概念速记
| 节点 | 前缀 | 大脑类比 | 作用 |
|---|---|---|---|
| event | e- | 海马 | 每条输入照原样记 |
| concept | c- | 新皮层 | 从反复事件抽象出模式 |
| intent | i- | **前额叶** | concept 簇密度达标时"结晶"成意图 |
| time | t- | — | 时间锚点 |

## 八种边类型
GROUNDS, CAUSES, TRIGGERS, REINFORCES, PART_OF, DERIVED_FROM, DEADLINE_FOR, RELATED_TO

## 跟翀哥体系对应
| CogniFold | 翀哥现有 |
|---|---|
| event 节点 | L3 daily 日志 |
| concept 节点 | L2 知识双向链接（但要更结构化） |
| intent 节点 | **缺失** — 这是最值得补的 |
| time 节点 | calendar |
| recall 机制 | L0.5 auto recall |
| proactive 涌现 | **目标** — 让 AI 主动想起该做什么 |

## 资源链接
- Live demo: https://opennorve.github.io/CogniFold/
- 论文: https://arxiv.org/abs/2605.13438
- Benchmark: https://huggingface.co/datasets/OpenNorve/CogEval-Bench
- 本地路径: `/Users/chongzhang/xiaoke//CogniFold/`
- Reddit 帖子：[原帖]（翀哥 00:32 发）