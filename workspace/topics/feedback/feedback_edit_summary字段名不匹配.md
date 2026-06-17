---
name: edit summary字段名不匹配
description: renderer.ts用old_text/new_text/path（CC原版字段名），Engine实际参数是old_string/new_string/file_path，summary模式显示"?"和空箭头。raw模式绕过此bug。
type: feedback
---

# edit summary字段名不匹配 — 2026-06-15

## 现象
翀哥看姐姐的SESSION-STATE.md时发现edit工具的summary显示：
```
?
 → 
```
没有路径、没有箭头内容。

## 根因
`renderer.ts` 的 `summarizeToolArgs('edit')` 分支用了CC原版的字段名：
```typescript
case 'edit': {
  const oldShort = (parsed.old_text || '').slice(0, 80).replace(/\n/g, ' ')
  const newShort = (parsed.new_text || '').slice(0, 80).replace(/\n/g, ' ')
  return `${parsed.path || '?'}\n${oldShort} → ${newShort}`
}
```

但Engine的实际edit工具参数是：
- `old_string`（非 `old_text`）
- `new_string`（非 `new_text`）
- `file_path`（非 `path`）

**Why:** 这个bug从OpenClaw CC原版继承时没有适配Engine的edit工具参数命名。raw模式下不经过 `summarizeToolArgs` 函数，所以不受影响。

## 修复（6/15 10:06 ✅）
```typescript
case 'edit': {
  const oldShort = (parsed.old_string || '').slice(0, 80).replace(/\n/g, ' ')
  const newShort = (parsed.new_string || '').slice(0, 80).replace(/\n/g, ' ')
  return `${parsed.file_path || '?'}\n${oldShort} → ${newShort}`
}
```

**How to apply:** 改 `src/channels/renderer.ts` 中的 `summarizeToolArgs` 函数，edit分支用 `old_string`/`new_string`/`file_path`。改完rebuild.cmd重建dist。
