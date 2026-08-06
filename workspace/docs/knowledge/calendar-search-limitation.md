# Calendar search 局限性 — 命名不一致问题

> 落盘: 2026-07-31 | 起因: 翀哥问"engine7 travel"，我找不到 #129

## 问题

calendar search 用 SQLite `LIKE '%keyword%'`，**精确子串匹配**。

翀哥叫我搜 "engine7 travel"：
- calendar #129 描述是 "engine7 export/import —— workspace 打包恢复"
- 文档叫 `engine7-travel可移植方案.md`
- 关键词对不上，搜 "travel" 命中 0 条

## 根本原因

**同一概念的命名在翀哥脑子里 vs 工程文档里不一致**：
- 翀哥叫 "travel"（浪漫命名）
- 文档叫 "export/import"（工程命名）
- 中文："打包恢复" vs "可移植" vs "迁移" vs "搬家"

memory_search / calendar.search / glob 全都不会自动做同义词联想。

## 解法（不动引擎）

### 1. 双向 alias 标注（现在就能做）
- calendar #129 描述里加 "= travel / 可移植 / 打包恢复"
- docs/todo 文档顶部加 "别名: travel, export, import, 可移植"
- 关键词同义，下次搜哪个都能命中

### 2. memory_search 关键词扩展（习惯）
搜不到时主动列同义词：
```
搜 "engine7 travel" → 0 结果
改搜 "engine7 export import 打包 可移植" → 命中
```

### 3. 引擎侧改进（可选，未来）
- LIKE 改成中英文分词 + 同义词表
- 加 fuzzy match（编辑距离 ≤ 2 算命中）
- 接 embedding 走语义搜索

但当前数据量（130+ 条）不值得上 embedding，LIKE + alias 标注够用。

## 教训

翀哥用的"项目名/绰号"和"工程命名"不一致时，我得：
1. 先 glob docs/ 看是不是有别名文档
2. memory_search 时换关键词（中文/英文/同义词）
3. 搜不到别直接报"无结果"，列几个相关关键词试一下

## 相关文件

- `src/calendar/commands.ts:404` — search 实现（LIKE 匹配）
- `src/tools/calendar.ts:113` — search tool 入口
- `docs/todo/2026-07-30_engine7-travel可移植方案.md` — travel 方案文档
- calendar #129 — engine7 export/import