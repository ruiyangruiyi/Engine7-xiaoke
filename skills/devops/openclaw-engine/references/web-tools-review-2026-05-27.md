# Web Tools Review (CC版, 2026-05-27)

小柯对比Claude Code源码 (`src-claudecode/src/tools/WebSearchTool/` + `WebFetchTool/`) review CC写的web_search和web_fetch。

## web-search.ts (2KB, 64行) — 评分 6/10

### CC版本 vs Claude Code版本

| 维度 | CC版 | Claude Code版 |
|------|------|--------------|
| 大小 | 2KB/64行 | 13KB/435行 |
| 搜索后端 | Tavily API | Anthropic原生web_search_20250305 API |
| 域名控制 | 无 | allowed_domains + blocked_domains |
| 搜索次数限制 | 无 | max_uses: 8 |
| 结果格式 | markdown字符串拼接 | 结构化数据(ToolUseID → SearchResult[]) |
| 进度回调 | 无 | onProgress + streaming |

### 🔴 P0 问题
1. `r.content?.slice(0, 200)` 搜索结果被截断到200字符，大量有用信息丢失
2. Claude Code返回完整content让LLM自己判断相关性

### 🟡 P1 建议
3. 缺 allowed_domains / blocked_domains — 对agent安全重要（防诱导搜索恶意域名）
4. 缺 max_uses 限制 — CC限制8次/轮，防搜索上瘾
5. 返回格式应更结构化（title+url列表），拼markdown字符串LLM解析不稳定
6. 可加 search_depth 参数（Tavily支持 basic/advanced）
7. 可返回搜索耗时

## web-fetch.ts (5.6KB, 173行) — 评分 7/10

### CC版本 vs Claude Code版本

| 维度 | CC版 | Claude Code版 |
|------|------|--------------|
| 大小 | 5.6KB/173行 | 9.3KB/318行 + utils.ts |
| HTML处理 | regex去标签→纯文本 | getURLMarkdownContent → Markdown |
| 提取能力 | 无 | applyPromptToMarkdown (小模型按prompt提炼) |
| PDF支持 | 无 | pdf-parse提取文字+持久化 |
| 权限控制 | 无 | preapproved hosts + 域名级权限 |

### ✅ 做得好的
- URL验证（长度/格式/用户名密码/hostname层级）
- 同域redirect判定 isPermittedRedirect
- 手动跟踪redirect（depth限制10次）
- HTTP→HTTPS自动升级
- 超时60秒 + abort信号支持
- 内容大小限制(10MB)

### 🔴 P0 问题
1. htmlToText太简陋 — 只去掉标签不保留语义：
   - `<li>`不加`•`、`<a>`丢href、`<h1>`不加`#`、`<pre>/<code>`无代码块、表格全毁
   - 应换 turndown npm包做HTML→Markdown转换，LLM阅读效果好10倍
2. `.replace(/\s+/g, ' ')` 把所有连续空白压成一个空格 — 代码、诗歌、格式化文本全毁

### 🟡 P1 建议
3. 缺 prompt 参数 — CC的WebFetchTool有prompt字段，让小模型提炼目标信息
4. 缺 PDF 支持 — CC用pdf-parse提取
5. 双重截断冗余 — MAX_MARKDOWN_LENGTH(100K)截一次再maxLength(5K)截一次，100K那次无用
6. htmlToText里的`&#\d+;`数字字符引用直接删了而不是解码

## 修复优先级
1. 🔴 web_fetch 换 turndown 库做 HTML→Markdown
2. 🔴 web_search 搜索结果不截断content
3. 🟡 web_search 加域名白/黑名单
4. 🟡 web_fetch 加 prompt 参数
