# CC Web Tools Review (2026-05-27 傍晚)

小柯review CC的web_search和web_fetch，对比Claude Code源码。

## Claude Code WebSearchTool (13.5KB/435行)

- **不是Tavily** — CC用的是Anthropic原生 `web_search_20250305` server tool，通过`queryModelWithStreaming`调LLM+web_search tool schema
- 参数: `query` (min 2) + `allowed_domains` + `blocked_domains`
- `max_uses: 8` — 限制每次最多8次搜索
- 结果格式: 结构化 `SearchResult[]` (title+url) + string摘要
- 流式进度: `onProgress` 回调，实时推送搜索查询和结果数
- 输出格式化: `mapToolResultToToolResultBlockParam` 统一拼markdown+链接

## Claude Code WebFetchTool (9.3KB/318行 + utils.ts)

- 参数: `url` + **`prompt`**（LLM告诉fetch要提取什么信息）
- HTML→Markdown: 用Turndown（不是简单去标签）
- 长页面处理: `applyPromptToMarkdown` 用小模型按prompt提炼
- PDF支持: pdf-parse提取文字
- redirect: 跨域redirect返回提示让LLM用新URL重试
- 权限: 预批准host列表 + 域名级别权限规则
- 二进制内容: 自动persist到磁盘

## CC web-search.ts Review (2KB/64行) — 6/10

### P0
- `r.content?.slice(0, 200)` 搜索结果截断200字符，太短

### P1
- 缺 `allowed_domains` / `blocked_domains`
- 缺 `max_uses` 搜索次数限制
- 返回拼markdown字符串，不如结构化数据

### P2
- 无搜索耗时统计
- 无 `search_depth` 参数

## CC web-fetch.ts Review (5.5KB/173行) — 7/10

### ✅ 做得好
- URL验证完整（长度/格式/用户名密码/hostname层级）
- 同域redirect判定 `isPermittedRedirect`
- 手动跟踪redirect（depth≤10）
- HTTP→HTTPS升级
- 超时60秒 + abort信号
- 内容大小限制10MB

### P0
- `htmlToText` 太简陋 — 只去标签不保留语义，代码/列表/表格全毁
- `.replace(/\s+/g, ' ')` 把格式化文本空白压平

### P1
- 缺 `prompt` 参数（小模型提炼长页面）
- 缺 PDF 支持
- 双重截断冗余（MAX_MARKDOWN_LENGTH 100K + maxLength 5K）

## 修复建议

1. **web_fetch 换 turndown** — `npm install turndown`，HTML→Markdown，LLM阅读效果10倍提升
2. **web_search 去掉 content 截断** — 让LLM看到完整搜索结果自己判断
3. **web_search 加 allowed_domains/blocked_domains** — 安全必需
