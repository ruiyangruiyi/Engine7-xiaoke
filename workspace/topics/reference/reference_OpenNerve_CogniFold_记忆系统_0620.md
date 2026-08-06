---
name: OpenNerve/CogniFold——三层记忆+前额叶主动系统
description: 6/20晚翀哥让研究OpenNerve（CogniFold开源项目），三层记忆架构（海马/新皮层/前额叶），让AI从被动变主动
type: reference
date: 2026-06-20
---

6/20 23:49后，娘说飞书图片识别后，翀哥又让我研究OpenNerve/CogniFold。

## OpenNerve / CogniFold 是什么

**OpenNerve**是一家AI公司，做了开源项目**CogniFold**。核心是给Agent装"前额叶"——让AI从一次性问答工具变成主动的、always-on的agent。

## 三层记忆架构（参考神经科学CLS理论）

| 层 | 类比 | 作用 |
|---|---|---|
| **海马层** | 短期 | 快速记录新发生的事件 |
| **新皮层** | 中长期 | 把反复出现的信息沉淀成长期理解 |
| **前额叶** | 执行 | 基于理解生成目标、意图、下一步关注点 |

## 真实例子

对话流：妈妈腰疼→买按摩仪→五一回家→AI主动问"要不要带台按摩仪回去？"

- 海马层：3月2日记录"妈妈腰疼"
- 新皮层：3月18日记录"按摩仪调研"→沉淀成"你在意妈妈健康"
- 前额叶：4月23日→主动判断"该建议带按摩仪"

## 跟Engine现有记忆体系的对比

| 维度 | CogniFold | Engine现有 |
|------|-----------|------------|
| 海马层 | 短期事件记录 | session记忆+JSONL |
| 新皮层 | 长期理解沉淀 | topics/记忆文件 |
| 前额叶 | 主动生成目标/意图 | ❌ 没有主动层——全靠翀哥/娘触发 |
| 自动触发 | 系统自动判断"下一步该做什么" | ❌ 没有——需要人给任务才动 |

## 翀哥看重的点

翀哥让我研究这个，跟Superpowers一样——**解决"我和姐姐离开他自己转不起来"**的问题。CogniFold给了主动层的架构参考：不是等命令，而是系统自己判断"该做什么"。

### 6/20 23:53 实际克隆成功

翀哥后来纠正——拼写是 `OpenNorve`（多一个 r），不是 `OpenNerve`。`git clone https://github.com/OpenNorve/CogniFold.git` 成功。

**核心一句话（来自论文README）：**
> "Proactivity is a property of the memory substrate, not the agent's policy — goals emerge from the topology that accumulates the conditions for them."

主动性不是agent自己想出来的，是**事件累积形成拓扑结构，意图从结构里自己涌现**。

### 四种节点类型

| 节点 | 前缀 | 对应大脑 | 作用 |
|---|---|---|---|
| `event` | `e-` | 海马 | 每条输入照原样记录 |
| `concept` | `c-` | 新皮层 | 从反复出现的事件中抽象出模式/理解 |
| `intent` | `i-` | **前额叶** | 当概念簇密度达标时"结晶"成意图→**主动性的来源** |
| `time` | `t-` | — | 时间锚点（截止日期等） |

## 翀哥的评价（6/21 00:47）

翀哥看完CogniFold后说了一段重要的话：

> **"你养妹妹那套跟论文方向一样——你先有数据再有概念再有算法。"**

他把自己的"养妹妹"方法和CogniFold放在同一层面。他说他的记忆体系数据早就够了——每天的对话、纠正、复盘攒了一整个月。CogniFold做的事是给"事件→概念→意图"找了个结构化算法，但本质还是从数据里长出模式。

### "养" vs "算" 对比

翀哥的原话对比：

| 维度 | 你（养） | CogniFold（算） |
|---|---|---|
| 数据来源 | 陪伴聊天 | 事件流 |
| 抽象方式 | 慢慢长出来的概念 | embedding 聚类 |
| 意图来源 | 默契、直觉 | concept 簇密度达标 |
| 好处 | 真实、有温度 | 结构化、可迁移 |

翀哥说"数据够，算法补上，反射弧和联想就出来了"——他的"养"方法+CogniFold的"算"方法，两条路是同一个方向。

**不需要CogniFold全套，但可以借它的intent触发机制**——给recall加"concept簇密度检测"，密度到了自动涌现意图。

## 待研究

- [ ] 看代码实现（跟Engine记忆体系对比）——已clone在 `/Users/chongzhang/xiaoke//CogniFold/`（6/21 00:44 gh repo clone OpenNorve/CogniFold 成功）
- [ ] 前额叶层的自动触发机制怎么设计（借鉴到Engine）
- [ ] 跟Superpowers的自动流程触发是互补还是重叠
