# CC Tool改动Review (2026-05-27 傍晚)

## 背景

小柯掉线期间CC对3个tool做了改进，爹让小柯回来review。

## CC改动清单

### 1. exec.ts — Windows Git Bash优先

**改动**：Windows上先找 `C:\Program Files\Git\bin\bash.exe`，找不到才fallback PowerShell

**小柯评价：8/10，改得好**
- ✅ LLM生成的都是Unix命令，Git Bash直接兼容
- ✅ WSL不受影响（process.platform === 'linux'）
- 🟡 suffix变量拼了exit code但没拼进output（L210-212 bug）
- 🟡 可以多查一个 `C:\Program Files (x86)\Git\bin\bash.exe`

**小柯原来不是这么做的** — 小柯直接判断win32就走PowerShell，CC改成Git Bash优先更聪明。

```typescript
// CC的实现 (L155-163)
if (isWindows) {
  const gitBash = 'C:\\Program Files\\Git\\bin\\bash.exe'
  if (fs.existsSync(gitBash)) {
    shell = gitBash
    shellArgs = ['-c', command]
  } else {
    shell = 'powershell.exe'
    shellArgs = ['-NoProfile', '-Command', command]
  }
}
```

### 2. read.ts — readFileState导出

**改动**：导出 `readFileState` Map，handler里记录每次读取的 `{ timestamp, content }`

**小柯评价：思路对，实现可优化**
- ✅ write的mtime守护需要read记录状态
- 🔴 存了完整content浪费内存，write只需要timestamp
- 🔴 没有清理机制，Map无限增长

```typescript
// CC的实现
export const readFileState = new Map<string, { timestamp: number; content: string }>()
// handler里:
readFileState.set(filePath, { timestamp: stat.mtimeMs, content })
```

建议改成：
```typescript
export const readFileState = new Map<string, { mtimeMs: number }>()
```

### 3. write.ts — mtime守护（乐观锁）

**改动**：import readFileState，写入前检查mtime是否变化

**小柯评价：✅ 逻辑正确**
- 乐观锁模式：read→记录mtime→write前检查mtime→变了就拒绝
- 新建文件不触发守护（readFileState里没记录）— 正确

```typescript
// CC的实现 (L162-171)
const readState = readFileState.get(filePath)
if (readState && fs.existsSync(filePath)) {
  const currentStat = fs.statSync(filePath)
  if (currentStat.mtimeMs !== readState.timestamp) {
    return { content: `文件在读取后被修改...`, isError: true }
  }
}
```

### 4. exec.ts — BLOCKED_ENV_KEYS 去掉 API_KEY/API_SECRET

**小柯评价：🔴 不应该改**
- 原来列表里有 `SECRET` 和 `TOKEN`，用 includes 匹配
- `SECRET` 已经覆盖 `API_SECRET`，`TOKEN` 已经覆盖 `API_TOKEN`
- 如果把 `API_KEY` 从过滤里去掉，`MY_API_KEY` 等环境变量会泄露给子进程
- **但实际看代码，BLOCKED_ENV_KEYS没变**，CC可能只是说了但没改

## suffix Bug详情

```typescript
// L210-212: suffix拼了但没用
const suffix = code !== 0
  ? `\nExit code: ${code ?? sig ?? 'unknown'}`
  : ''
// ... suffix 从来没被拼进 output
```

修复：在resolve前加 `if (suffix) output += suffix`

## tools目录整理操作记录

1. 删6个旧版：`rm edit.ts read.ts write.ts exec.ts grep.ts glob.ts`
2. 改名：`mv claude-edit.ts edit.ts`（6个）
3. 清backup：`rm -rf backup/`
4. features.ts import路径天然匹配，不用改
5. 只commit src/tools/下变更：`git add src/tools/*.ts`
6. commit: `084faf6`
