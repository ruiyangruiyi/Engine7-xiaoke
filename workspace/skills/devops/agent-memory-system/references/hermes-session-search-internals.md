# Hermes session_search 实现详解

源码路径：
- 工具入口：`tools/session_search_tool.py`（605行）
- 数据层：`hermes_state.py`（SessionDB类，FTS5+trigram）
- Agent调用：`run_agent.py:9697` / `run_agent.py:10300`

## 架构概览

session_search = **SQLite FTS5全文搜索 + 辅助LLM摘要**，两阶段流水线：
1. FTS5在所有历史session消息里做全文检索
2. 匹配到的session对话发给辅助模型（`auxiliary.session_search`）生成聚焦摘要

## 数据存储

所有session存在 `~/.hermes/state.db`（SQLite，WAL模式并发读写）。

核心表：
- `sessions` — 元数据（id, source, user_id, model, system_prompt, parent_session_id, started_at, ended_at, title, token统计, 费用等）
- `messages` — 完整消息（id, session_id, role, content, tool_call_id, tool_calls, tool_name, timestamp, reasoning等）
- `messages_fts` — FTS5虚拟表（默认unicode61分词器，英文搜索）
- `messages_fts_trigram` — trigram FTS5虚拟表（CJK中文搜索）

FTS5索引通过触发器自动同步：messages表INSERT/UPDATE/DELETE时自动更新两个FTS5表。索引内容 = `COALESCE(content, '') || ' ' || COALESCE(tool_name, '') || ' ' || COALESCE(tool_calls, '')`。

## 搜索流程（session_search_tool.py）

### 模式1：无query → 浏览最近session
- `_list_recent_sessions()` 直接查DB
- `list_sessions_rich(order_by_last_active=True)` 获取最近session
- 排除当前session及其parent lineage
- 排除有parent_session_id的子session（委托任务）
- 返回标题/时间/source/message_count/preview
- **零LLM开销，秒回**

### 模式2：有query → 关键词搜索

```
1. _sanitize_fts5_query() 清洗查询
2. db.search_messages() FTS5搜索，取50条原始匹配
3. 按session_id去重，保留top N（默认3，上限5）
4. _resolve_to_parent() 子session追溯父session
5. 排除当前session lineage
6. 加载每个session完整对话 → _format_conversation()
7. _truncate_around_matches() 智能截断到100K字符
8. 并行调LLM做摘要（_summarize_session），信号量限并发
9. 返回 per-session 摘要 + 元数据
```

## CJK中文搜索三路分支 ⭐

FTS5默认unicode61分词器把CJK拆成单字，"大别山项目"→"大 AND 别 AND 山..."，效果很差。

`search_messages()` 根据`_contains_cjk()`检测结果走三路：

| 条件 | 策略 | 表 | 原理 |
|------|------|----|------|
| 非CJK（英文等） | FTS5 unicode61 | messages_fts | 正常分词，支持布尔/短语/前缀 |
| CJK ≥ 3个字符 | FTS5 trigram | messages_fts_trigram | 3字节滑动窗口子串匹配 |
| CJK 1-2个字符 | LIKE子串 | messages表直查 | trigram需要≥3个CJK字符 |

CJK检测：遍历字符检查Unicode范围（4E00-9FFF/3400-4DBF/20000-2A6DF/3000-303F/3040-309F/30A0-30FF/AC00-D7AF）。

trigram路径的特殊处理：对非布尔运算符(AND/OR/NOT)的token加双引号，防止FTS5特殊字符报错。

## 查询清洗（_sanitize_fts5_query）

6步清洗管道：
1. 提取并保护已配对的双引号短语
2. 剥离未匹配的FTS5特殊字符 `+{}()\"^`
3. 合并重复`*`，移除前导`*`（前缀搜索至少需要1个字符）
4. 移除开头/结尾的悬空布尔运算符
5. 对未引用的连字符/点号词加引号（如 `chat-send` → `"chat-send"`）
6. 恢复保护的引号短语

## 智能截断（_truncate_around_matches）

当对话超过100K字符时，选覆盖最多匹配位置的窗口：
1. **优先找完整短语**匹配位置
2. **其次找200字符内所有关键词共现**位置
3. **最后找单个词**位置
4. 窗口偏移：25%前 + 75%后

## Session lineage处理

- `_resolve_to_parent()` 沿 parent_session_id 链追溯根session
- 委托任务（delegate_task）的细节存在子session，但用户对话在父session
- 当前session的整个lineage都排除，避免搜到自己

## LLM摘要（_summarize_session）

- 使用 `auxiliary.session_search` 配置的模型（默认跟主chat模型同provider）
- `async_call_llm(task="session_search", ...)` 路由
- temperature=0.1，max_tokens=10000
- 3次重试，指数退避
- prompt要求：聚焦搜索主题，保留具体细节（命令/路径/错误信息），过去时事实性总结
- 并发控制：`_get_session_search_max_concurrency()` 默认3，上限5

## 与姐姐topic-recall的对比

| 维度 | 小柯 session_search | 姐姐 topic-recall |
|------|-------------------|------------------|
| 存储 | SQLite + FTS5索引 | JSONL + manifest索引文件 |
| 搜索 | 实时FTS5全文检索 | LLM预先提取→topic文件→关键词匹配 |
| 召回 | 搜索+LLM即时摘要 | topic文件直接注入prompt |
| 中文 | trigram三路分支 | OpenClaw自有处理 |
| 记忆粒度 | session级（整段对话） | topic级（主题片段） |
| 成本 | 每次搜索消耗LLM token做摘要 | 预提取后零边际成本 |
| 路线 | 搜索引擎模式 | 知识库模式 |

## 已知问题

- **活跃session搜不到**（5/14发现）：cron记忆提取用session_search搜正在进行的对话，结果为零。因为"活跃session"的消息可能还没被FTS5索引刷新覆盖到，或者session_search排除了当前session lineage。姐姐不受影响因为直接读JSONL文件。
- **limit强制上限5**：`max(1, min(limit, 5))`，模型传再多也只能返回5个session。
