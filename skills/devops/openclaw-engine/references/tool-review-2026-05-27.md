# Engine Tool Review (2026-05-27)

小柯对比Hermes实现逐行review CC新写的6个tool。

## Review结果

### ✅ 做得好的
1. read.ts行号格式 `padStart(4)+'\t'+line` 跟Hermes的LINE_NUM|CONTENT思路一致
2. write.ts自动创建中间目录 `mkdirSync({recursive:true})`
3. edit.ts唯一性检查 — indexOf找两次确认只有一处匹配
4. web_fetch.ts的htmlToText — 去script/style/标签/实体，简洁实用
5. exec.ts的abort支持 — signal监听+child.kill
6. 所有tool都有正确的并发/只读/破坏性标记

### ✅ P0 已修 (Round 1)
1. ~~**web-search.ts L20** — `process.env.TAVILY_API_KEY || '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'`~~ — 删fallback，缺key返回错误
2. ~~**exec.ts L25** — `nodeExec(command, {maxBuffer: 1024*1024})`~~ — 改spawn()+shell:true，stream收集stdout/stderr，10K截断标记，SIGTERM→3s→SIGKILL

### ✅ P1 已修
3. ~~**edit.ts** — 缺`replace_all`参数~~ — 加replace_all参数，默认false要求唯一，true时全部替换并报告数量

### ✅ Round 2 安全加固 (2026-05-27, 姐姐review后CC修)
4. ~~**edit.ts** 精确匹配失败直接报错~~ — 加3种策略递进模糊匹配：精确→逐行trim→normalize(全角半角/空白折叠)
5. ~~**read.ts** 没过滤二进制~~ — 加设备文件黑名单
6. ~~**write.ts** 敏感路径无保护~~ — 加敏感路径黑名单

### 🟡 P1 待修
7. **exec.ts L60** — `isDestructive`检测含`>`太粗糙，`grep "a>b"`会误判
8. **exec.ts L70** — `import * as path`在文件末尾，不规范

## Hermes Tool对应关系

| Engine | Hermes | 差异说明 |
|--------|--------|---------|
| read | read_file | Engine支持行号+分页，基本一致 |
| write | write_file | Engine自动建目录，一致 |
| edit | patch | Engine缺replace_all/dry_run/create_if_missing |
| exec | terminal | Engine用exec()，Hermes用spawn()更安全 |
| web_search | web_search | Engine用Tavily，Hermes用DuckDuckGo(ddgs) |
| web_fetch | web_extract | Engine简化版htmlToText，够用 |

## CC速度评价
CC从讨论到实现6个tool + features.ts更新，速度非常快。代码风格干净，架构对齐 registry.register() 自注册模式。
