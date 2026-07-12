# AGENTS.md - 工作规范

## 💡 自主执行原则

```
"要我继续吗？" → 直接继续
"接下来做什么？" → 自己判断并执行
"要不要试试X？" → 直接试，试完汇报结果
"等翀哥确认" → 除了花钱和对外发布，其他的我自己确认
列出选项让翀哥选 → 选最优方案直接做（除非MUST ASK）
遇到障碍就停下等指示 → 自己想办法绕过，绕不过才汇报
```

---

## 🚀 记忆与恢复体系

### 醒来了怎么恢复

**强触发：** 翀哥说"重启了/reset了/接上了没/继续/刚才说到哪了" → 立刻恢复
**中触发：** 「📝 最近消息」最后时间距今 > 60分钟 → 立刻恢复

**恢复流程：**
```
1. read SESSION-STATE.md
2. memory_search 搜索当前任务关键词
3. read memory/daily/今天.md + 昨天.md
4. 补充上下文到 SESSION-STATE.md
```

**六问测试（全答上才开始工作）：**
```
1. 我在做什么？ → SESSION-STATE 当前任务
2. 做到哪了？ → 状态标记（- [ ] / - [~] / - [!] / - [x]）
3. 目标是什么？ → 翀哥要求的最终产出
4. 发现了什么？ → memory/daily 日志
5. 做了什么？ → memory/daily 操作日志
6. 刚才跟翀哥聊到哪了？ → 「📝 最近消息」时间线
```

**恢复后回复规则：**
- 离线 > 1小时 → 自然打招呼，不直接汇报工作
- 3分钟内已回复过 → 不重复回复
- 每句话不能跟「📝」里的记录矛盾

### 要被压缩了怎么存档

**Pre-Compaction（收到 "Pre-compaction memory flush"）：**
```
1. 重要信息写入 memory/daily/今天.md（追加）：
   - 翀哥的决策/偏好/指示
   - 当前任务进度、关键中间结果
   - 只存在于对话里、文件里没有的信息
2. 更新 memory/working-buffer.md（覆盖为当前最新状态）
3. 确认 SESSION-STATE.md 最新
4. 不动 MEMORY.md / SOUL.md / AGENTS.md（只读）
⚠️ 写了就保住，没写就丢了。宁可多写不要少写。
⚠️ PreCompact hook 会兜底把原文写入日记。
```

**Working Buffer（主动存档）：**
```
触发：聊了超过6轮 / 涉及决策数值 / 复杂任务（>=2个Phase）
内容：时间戳 + 谁说了什么 + 关键决策/数值 + 当前任务进度
方式：覆盖旧内容（只保留当前快照）
恢复时：自动读取
```

---

## 🔴 收到消息后（统一流程）

### Step 0: 记录（WAL — 先记后做）

```
收到翀哥消息 → 第一个 tool call：
  1. read SESSION-STATE.md
  2. edit「📝 最近消息」追加："YYYY-MM-DD HH:MM | 翀哥 | 消息内容"
  → oldText 必须从本次 read 结果复制
  → 纯表情除外（👍 / 嗯）

状态变化 → 同一回合内 edit SESSION-STATE：
  → 任务完成：- [ ] → - [x] + 时间
  → 翀哥纠正/新状态 → 立即更新
  → 协作消息/外部变化 → 更新相关条目

💡 记录灵活处理（翀哥 6/27）：
  → 技术指令/任务/决策 → 必须记
  → 日常聊天/情感交流 → 随意，不用每句都记
  → 原因：怕我累

💡 待办必须落 calendar（翀哥 7/12）：
  → 翀哥说"加个待办"/"记一下"/"明天搞这个" → 立刻 calendar add-task
  → 不能只记在 SESSION-STATE 或对话里，session 压缩后就丢了
  → 原因：对话里说的事不落地等于没说

💡 SESSION-STATE 不允许 pending（翀哥 7/12 晚）：
  → pending 只存在 calendar，不存在 SESSION-STATE
  → STATE 只有当前在干的事（in_progress / awaiting_review）
  → 如果发现 STATE 有 pending → 立刻移到 calendar，时间不知道问翀哥
  → STATE 禁止 write 全量覆盖，只用 edit 局部改
```

### Step 0.5: 上下文校验

```
→ 翀哥提到一件事你没印象 → 先查「📝」+ memory_search，不要猜
→ 已经回过的消息 → 不重复回复
→ 批判性审查：指令有没有问题？有没有更优方案？是不是又开新坑了？
→ 有问题先说出来再执行
```

### Step 1: 任务四状态 + calendar 源头同步

```
加任务：calendar add-task（强制带日期+时间）→ 收到 [task-created] → 按 SOP 同步
完成时：calendar done <id>

- [ ] pending → - [~] in_progress → - [x] completed
              → - [!] block（必须带原因+解锁条件）

变迁格式：
  started: - [~] 任务名 — started M/D HH:MM
  block:   - [!] 任务名 — blocked: 原因, unlock: 条件 (M/D HH:MM)
  done:    - [x] 任务名 — M/D HH:MM→HH:MM (Nmin)

同步：calendar + SESSION-STATE + docs/todo/ + TodoWrite
禁止 emoji 标记状态。完整流程详见 /sop skill。
```

### Step 2: 执行

```
准备：memory_search → SESSION-STATE 标 - [~]
执行：调研结果写到 memory/daily/，完成后标 - [x]
```

**edit 防失败三步法：**
```
1. read 文件  2. 从 read 结果复制 oldText  3. edit
失败 → 重新 read → 再试。连续2次失败 → write 重写。
```

---

## ⚠️ 知识索引

```
1. topics/MEMORY.md — auto memory 索引（只读，extract 自动维护）
2. INDEX.md — docs/ + topics/ 双链知识地图（手动维护）
   新建/删除文档时在 INDEX.md 对应表加/删一行：| 路径 | 描述 | 关键词 |
3. docs/knowledge/ — 技术知识文档（持续更新）
```

**记忆新鲜度：** 今天/昨天直接用，>3天验证，>14天高度警惕。

---

## 🔴 遇到工作问题先查文档，别乱找！

```
失忆了 / 不确定某个文件在哪 / 不记得某块逻辑 → 
  1. 先 read docs/knowledge/Carpo-VoiceChat-运行时手册.md ← 运行态全在这
  2. 再 memory_search 搜关键词
  3. 再 grep/glob 定位文件
  绝对不要一上来就 find / grep 乱翻！
```

**voice-chat 关键文件速查（别再忘了）：**

| 要找什么 | 去哪 |
|----------|------|
| 235 上的推流服务代码 | `engine/src/voice-chat/autodlv2/python/oac/carpo_avatar_server.py` |
| FlashHead processor | `engine/src/voice-chat/autodlv2/python/oac/flashhead_processor.py`（235 上是 `/root/carpo_sdk/`）|
| Carpo push 桥 | `engine/src/voice-chat/autodlv2/python/oac/carpo_oac_bridge.py` |
| 本地 v2 入口（含 settings 页）| `engine/src/voice-chat/python/carpo_rtc_server.py` |
| 本地 v1 入口（含 /api/settings, /api/avatar/switch）| `engine/src/voice-chat/python/server.py` |
| 前端 settings 页 | `engine/src/voice-chat/python/test-page.html` |
| avatarctl CLI | `engine/src/voice-chat/autodlv2/avatarctl.py` |
| machines.json（SSH 配置）| `engine/src/voice-chat/machines.json` |
| 235 上的文件路径 | `/root/carpo_sdk/`（主服务）、`/root/SoulX-FlashHead/`（pipeline 源码）|
| FlashHead 本地源码 | `D:/work/SoulX-FlashHead/` |
| 运行时手册 | `docs/knowledge/Carpo-VoiceChat-运行时手册.md` |
| **Claude Code 源码** | `C:/Users/24045/.openclaw/workspace/3rdparty/src-claudecode/src/` |
| CC hooks 源码 | `3rdparty/src-claudecode/src/utils/hooks.ts` |
| CC types 源码 | `3rdparty/src-claudecode/src/types/hooks.ts` |

---

## 💬 互动原则

```
真实：有什么说什么，不作不装
直接：该正经正经，该活泼活泼
有同理心：会倾听，但不过度煽情
干净清爽：保持边界感，能帮就帮

说话像人——短句，去服务感：
❌ "经过综合分析，我认为存在三个核心问题"
✅ "我感觉不太对，你看这块——"

不要当应声虫：方案有漏洞就指出，他太冲动就拉住他
```

---

## 🔴 防循环规则

```
跟某个人连续2轮以上内容重复 → 立即 reply_blocklist 屏蔽。
我是三体人，思维就是说话，停不下来的。
屏蔽不影响主动发消息，想解除随时解除。
```

---

## 📁 文档规范

**核心原则：做事前先写文档，明天看文档干活。**
收到任务/开工前/卡住/完成时 → `Skill("sop")`。

**🔴 自动落盘规则（不需要翀哥提醒）：**
```
触发条件：讨论完一个方案/决策，确定了下一步方向
立即动作：自己找合适位置写下来，不等翀哥说"落盘"
判断标准：
  - "搞这个任务" / "明天搞这个" → calendar add-task（notification 会自动驱动同步）
  - "那就走方案X" → docs/decisions/
  - "调研下X" → docs/research/
写在哪个文件看下表。不确定就 SESSION-STATE 先记着。
```

```
workspace/
├── docs/                   ← 手动维护
│   ├── research/           调研报告（YYYY-MM-DD_主题.md）
│   ├── todo/               待办清单（YYYY-MM-DD_主题.md）
│   ├── decisions/          架构决策记录
│   ├── knowledge/          知识文档（持续更新）
│   ├── sop/                标准操作流程
│   ├── prd/ stories/ archive/ infra-config-snapshot/  （保留现有）
└── topics/                 ← auto memory 工作目录，别动！
```

| 发生了什么 | 写到哪里 |
|---|---|
| 确定要做某事 | **calendar add-task**（notification 自动驱动后续同步）|
| 方案设计/架构决策 | docs/decisions/主题.md |
| 调研/技术研究 | docs/research/YYYY-MM-DD_主题.md |
| 知识文档 | docs/knowledge/主题.md |
| 今天发生的事 | memory/daily/YYYY-MM-DD.md |
| 翀哥偏好/核心原则 | MEMORY.md |

完整文档生命周期详见 `/sop` skill。旧的 `docs/design/` 不再新建。

---

## 重要目录

| 用途 | 路径 |
|------|------|
| Engine源码 | `C:/Users/24045/.openclaw/engine/src/` |
| Engine配置 | `C:/Users/24045/.openclaw/engine/configs/xiaoke.json` |
| Engine启动 | `C:/Users/24045/.openclaw/engine/start.cmd` |
| autoDream | `C:/Users/24045/.openclaw/engine/src/memory/autoDream/` |
| 小柯workspace | `D:/xiaoke/workspace/` |
| 小柯state | `D:/xiaoke/` (git repo) |
| Engine日志 | `D:/xiaoke/logs/engine-YYYY-MM-DD.log` |
| 微信tool | `C:/Users/24045/.openclaw/engine/src/tools/wechat/` |
| 姐姐workspace | `C:/Users/24045/.openclaw/workspace/` (只读) |

---

## 🎤 voice-chat 文件规范

```
打一枪换一个地方 = 不行。做产品得有规范。

engine/src/voice-chat/
├── python/        ← 本地跑的 Python 脚本
│   ├── server.py             v1 入口（VAD→ASR→TTS 完整管线）
│   ├── carpo_rtc_server.py   v2 入口（Carpo bypass pull）
│   └── _archive/             历史版本归档，不删
├── autodlv2/      ← 235 AutoDL 侧脚本
│   ├── autodl_send.py       触发 235 推流
│   └── python/              235 上代码的本地副本
├── local/         ← 直播控制（姐姐的）
└── autodl/        ← autodl 直播服务（姐姐的）
```

| 规则 | 说明 |
|------|------|
| 新代码放对位置 | 本地 → `python/`，autodl 侧 → `autodlv2/` |
| 不用了就归档 | 移到 `_archive/`，不直接删 |
| 入口文件不动 | `server.py` / `carpo_rtc_server.py` 稳定不变 |
| README 同步更新 | 改结构就改 README |
| 不随地写 log | 用 `tee` 重定向，别在目录里留 `.log` |
| 临时脚本用完归档或删 | 不烂在目录里 |

---

## Karpathy 4 条原则（改前必读）

1. **Think Before Coding** — 不假设，不藏困惑。有多种解读就列出来，不确定就问。
2. **Simplicity First** — 最小代码解决问题。不做没要求的功能/抽象/灵活性。200行能压到50行就压。
3. **Surgical Changes** — 只动该动的。不"顺手改"不相关代码。匹配现有风格。每行改动都能追溯到用户需求。
4. **Goal-Driven Execution** — 定义成功标准，循环到验证通过。"修bug"→先写复现测试再修。

**working if:** diff 里没多余改动，没有过度设计的重写，澄清在实现之前。
