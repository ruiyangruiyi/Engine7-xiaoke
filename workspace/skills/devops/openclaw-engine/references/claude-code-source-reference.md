# Claude Code 源码位置 & Tool架构参考

**最后更新**: 2026-05-27

## 源码本地路径（翀哥workspace，已确认存在）

```
/Users/chongzhang/.openclaw\workspace\start-claude-code\
/Users/chongzhang/.openclaw\workspace\3rdparty\src-claudecode\src\tools\
```

两个路径指向同一份源码，用哪个都行。

## Tool源码文件清单

| Claude Code Tool | 核心文件 | 大小 | 关键函数 |
|----------------|---------|------|---------|
| BashTool | `BashTool/BashTool.tsx` | 160KB | shell进程spawn、安全扫描 |
| FileEditTool | `FileEditTool/FileEditTool.ts` | 20KB | findActualString、applyEditToFile、getPatchForEdits |
| FileReadTool | `FileReadTool/FileReadTool.ts` | 39KB | BOM检测、编码感知、重复读循环 |
| FileWriteTool | `FileWriteTool/FileWriteTool.ts` | 15KB | 原子写入、敏感路径、文件修改检测 |
| GrepTool | `GrepTool/GrepTool.ts` | 20KB | ripgrep调用、分页、路径相对化 |
| GlobTool | `GlobTool/GlobTool.ts` | 6KB | glob模式、修改时间排序 |

## 关键算法摘录（可直接移植到engine）

### findActualString (FileEditTool/utils.ts:73-93)
```typescript
function findActualString(fileContent, searchString):
  1. 精确匹配 fileContent.includes(searchString)
  2. 引号规范化匹配：normalizeQuotes(searchString) 在 normalizeQuotes(fileContent) 中查找
  3. 返回实际匹配到的字符串（包含原始引号风格）
```

### applyEditToFile (FileEditTool/utils.ts:206-228)
```typescript
function applyEditToFile(content, old, new, replaceAll):
  - replaceAll=true: content.replaceAll(old, new)
  - replaceAll=false: content.replace(old, new)
  - 删除时处理尾部换行：如果 old不以\n结尾 但 content包含 old+'\n'，删除时去掉\n
```

### preserveQuoteStyle (FileEditTool/utils.ts:104-136)
```typescript
// 当old_string通过引号规范化匹配时，对齐new_string的引号风格到文件
// 检测文件用的是弯单引号还是直引号，new_string中对应的引号字符做替换
```

### isBlockedDevicePath (FileReadTool.ts:98-128)
```typescript
const BLOCKED = new Set([
  '/dev/zero', '/dev/random', '/dev/urandom', '/dev/full',
  '/dev/stdin', '/dev/tty', '/dev/console',
  '/dev/stdout', '/dev/stderr',
  '/dev/fd/0', '/dev/fd/1', '/dev/fd/2',
])
// 加上 /proc/self/fd/0-2 等Linux别名
```

### ripgrep调用模式 (GrepTool.ts:330-441)
```typescript
const args = ['--hidden']
// 排除VCS目录: --glob '!.git'
// 限制行宽: --max-columns 500
// content模式加: -n(行号) -C(上下文行数)
// files模式: -l
// count模式: -c
// pattern以-开头: -e pattern（防误认为flag）
```

## engine tool接口（已适配）

Claude Code用`buildTool()`，engine用`registry.register({})`，字段对应关系：

| Claude Code | engine |
|------------|--------|
| `name` | `name` |
| `description()` | `description` |
| `inputSchema()` | `schema` |
| `call(input, context)` | `handler(args, ctx)` |
| `isConcurrencySafe()` | `isConcurrencySafe(args)` |
| `isReadOnly()` | `isReadOnly(args)` |
| `isDestructive()` | `isDestructive(args)` |
| `interruptBehavior()` | `interruptBehavior()` |

## 注意事项

1. **不要照抄UI部分** — Claude Code有大量UI渲染代码(engine不需要)
2. **权限系统跳过** — engine用workspace sandbox，CC的toolPermissionContext不需要
3. **LSP通知跳过** — CC有LSP服务器通知，engine不需要
4. **analytics跳过** — CC有事件追踪，engine不需要
5. **优先移植算法** — fuzzy match、ripgrep调用、设备文件检测等核心逻辑
