---
name: contacts.md ESM bundle坑——require('fs')在esbuild里被shim成空对象
description: 6/18 08:56姐姐报告contacts.md哈希表反查没生效，根因是handle-query.ts里`require('fs')`在esbuild ESM bundle里被shim成`__require('fs')`返回空对象，readFileSync/existsSync静默失败；改用顶部已import的函数修复
type: feedback
date: 2026-06-18
---

## 6/18 08:56 姐姐紧急反馈
翀哥重启后从微信发消息，meta头名字还是原始ID `o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat`，contacts.md哈希表反查没生效。

日志里**完全没有 `[meta] contacts.md loaded`**——`loadContactMap` 要么没被调到，要么 `require('fs')` 静默失败。

## 根因
`handle-query.ts` 里我用了 `require('fs')` 而不是顶部已经 `import` 的 `readFileSync`/`existsSync`。esbuild 把 TS bundle 成 ESM 时，`require` 被 shim 成 `__require('fs')`——返回空对象或抛异常被 catch 吞掉，导致 `readFileSync`/`existsSync` 调用静默失败，contactMap 永远是空 Map，`dict.get(senderId)` 全 miss → fallback 到原始 ID。

## 修复
改用顶部已 import 的 `readFileSync`/`existsSync`（`existsSync12`/`readFileSync14` 是 esbuild 内联的 import 别名），不再调 `require('fs')`。已 rebuild + 提交。

**Why:** esbuild bundle 时 `require()` 不是真 Node require，是 shim。在 ESM bundle（type=module）下走 `import` 才是真的。

**How to apply:**
1. **TS/JS 代码里不要再用 `require()`**——顶部已经 import 的函数直接调用
2. esbuild bundle 后模块作用域变了，模块级单例缓存（如 `let contactMap = null`）也要小心——bundle 后可能被 hoist 或共享
3. 改完看 dist 里的实际代码——不是 source 是 dist 在跑
4. 如果"应该执行但日志没出现"，先怀疑函数没被调到（路径/scope/导入问题），再怀疑逻辑错
