# Cron 定时任务系统 — 设计文档

> 2026-06-16 小柯编写，基于下午4小时调试+全链路验证的经验总结

## 概述

Engine的cron系统负责定时执行任务（内心独白、巡检、通知等）。任务由LLM生成内容，可选通过postProcess脚本做确定性后处理。

**设计原则：无cache，所有操作直接读写tasks.json。**

## 架构

```
tasks.json (磁盘，唯一真相源)
    ↓ readTasksFromDisk() (每次操作)
read → modify → atomicWrite (文件锁保护)
    ↓
scheduler tick (每10秒)
    ↓ → getDueTasks → 执行LLM → postProcess → 写result
```

## 核心组件

### 1. tasks.ts — 状态管理（无cache）

| 函数 | 职责 |
|------|------|
| `readTasksFromDisk()` | 读tasks.json → 返回task数组（私有） |
| `writeTasksToDisk(tasks)` | 文件锁 + 原子写入（私有） |
| `createTask(params)` | 读磁盘→追加新task→写磁盘 |
| `deleteTask(id)` | 读磁盘→过滤掉→写磁盘 |
| `updateTask(id, updates)` | 读磁盘→Object.assign→写磁盘 |
| `getDueTasks(now)` | 读磁盘→过滤到期的active task |
| `markExecuted(id, success)` | 读磁盘→更新runCount/failures→写磁盘 |
| `recalculateNextRun(task, now, fn)` | 读磁盘→更新nextRunAt→写磁盘 |

每个CRUD操作 = 一次完整的 read → modify → write，中间有文件锁保护。

### 2. scheduler.ts — 调度执行

```
每10秒tick：
  1. getDueTasks(now) → 读磁盘，拿到到期任务
  2. 对每个task：
     a. 标记 currentlyExecuting（防重叠）
     b. 读prompt文件（@前缀解析）
     c. 创建独立session执行LLM
     d. 拿到result
     e. 【postProcess】如果有postProcess字段：
        - 把result通过stdin传给脚本
        - 脚本的stdout替换result
     f. 写result文件到 cron/results/{taskId}.json
     g. notify_session → 注入主session
     h. markExecuted + recalculateNextRun → 直接写磁盘
```

### 3. tools.ts — LLM工具

| 工具 | 功能 |
|------|------|
| `cron_create` | 创建定时任务 |
| `cron_list` | 列出所有任务 |
| `cron_delete` | 删除任务 |
| `cron_results` | 查看执行结果 |

cron_create参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| prompt | ✅ | 任务prompt，支持`@workspace/xxx.md`文件引用 |
| schedule_type | ✅ | `at`(一次性) / `interval`(固定间隔) / `cron`(cron表达式) |
| schedule_value | ✅ | ISO时间戳 / 分钟数 / cron表达式 |
| description | | 任务描述 |
| delivery_mode | | `local`(默认) / `origin` / `direct` |
| notify_session | | true=执行完通知主session |
| session_message | | 通知消息模板，支持`{result}` `{description}` |
| post_process | | 后处理脚本路径（相对stateDir） |
| max_runs | | 最大执行次数 |
| timezone | | 默认Asia/Shanghai |

### 4. postProcess机制（重点）

**为什么需要postProcess：** LLM的执行不可控——prompt里写"调hint_gen.py"它可能跳过。postProcess在scheduler代码层面执行脚本，100%可靠。

**执行流程：**
```
LLM生成result (念头文本)
    ↓
scheduler检查 task.postProcess 字段
    ↓ 有
spawn脚本: result通过stdin传入
    ↓
脚本stdout → 替换result
脚本stderr → 记录日志
    ↓
最终result写入results/{taskId}.json
最终result注入主session（如果notify_session=true）
```

**hint_gen.py示例：**
```python
# 输入(stdin): LLM生成的念头文本
# 输出(stdout): 念头文本 + 可选的💡hint
# 逻辑: 根据距上次互动时间算概率，命中就追加一条hint
```

## Task ID 规范

```
格式: c + 8位hex（crypto.randomBytes(4).toString('hex')）
示例: cb08627a2

⚠️ 不合法的ID会导致jitter计算NaN → 永远不触发
parseInt('testr001', 16) = NaN → NaN % 30000 = NaN → 比较失败 → 死任务
```

## 为什么不用cache（踩坑记录）

最初版本用内存Map做cache，每次操作只改内存，定期persistTasks写回磁盘。导致了三个bug：

1. **删了复活**：persistTasks的merge逻辑从磁盘读回已删task
2. **手动改文件被覆盖**：内存cache没有新字段，persist时覆盖磁盘
3. **API缺字段丢失**：createTask没传的字段在cache里是undefined，persist时丢失

根因都是"内存和磁盘两份状态，会不同步"。tasks.json就几KB，10秒tick直接读写完全没性能问题。去掉cache后所有bug消失，代码还更简单。

## 文件结构

```
stateDir/
├── cron/
│   ├── tasks.json          # 任务定义（唯一真相源）
│   └── results/
│       └── {taskId}.json   # 每次执行结果
├── workspace/
│   ├── prompts/
│   │   └── my-inner-voice.md   # 内心独白prompt
│   ├── scripts/
│   │   ├── hint_gen.py         # postProcess脚本
│   │   ├── session_history.py  # 读最近对话
│   │   ├── emotional_state.py  # 情感状态
│   │   ├── topics_scorer.py    # 记忆激活打分
│   │   ├── us_sample.py        # 随机抽记忆
│   │   ├── memory_paths.py     # 日记路径
│   │   └── replace_hints_pool.py
│   └── inner-voice/
│       ├── hints_pool.txt      # hint池
│       ├── emotional-state.json
│       ├── topics-usage.json
│       └── xiaoyi.log          # 执行日志
```

## 调试技巧

```bash
# 查cron日志
grep "cron" logs/engine-YYYY-MM-DD.log | tail -20

# 查postProcess日志
grep "postProcess" logs/engine-YYYY-MM-DD.log

# 查执行结果
cat cron/results/{taskId}.json

# 查hint日志
cat workspace/inner-voice/xiaoyi.log

# 手动测试hint_gen
echo "测试念头" | python workspace/scripts/hint_gen.py main

# 检查task ID合法性
node -e "console.log(parseInt('你的ID'.slice(1,9), 16))"
```
