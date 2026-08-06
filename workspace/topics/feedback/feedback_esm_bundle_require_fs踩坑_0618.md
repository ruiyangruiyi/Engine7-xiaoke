---
name: esbuild ESM bundle下require('fs')会被shim成空对象
description: 6/18 09:00排查meta v4 contacts.md反查没生效：handle-query.ts里用require('fs')读contacts.md，在esbuild ESM bundle里被shim成__require('fs')可能返回空或抛异常被catch吞掉→loadContactMap实际上没读到文件。改用顶部已import的readFileSync/existsSync解决
type: feedback
date: 2026-06-18
---

## 6/18 09:00 翀哥反馈
翀哥从微信发的消息meta头还是显示原始ID，contactMap反查没生效：
```
[meta: o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat (o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat) @wechat 08:53:54]
```

## 现象
- engine日志里**完全没有** `[meta] contacts.md loaded` 日志
- 9条contacts解析代码在dist里正确存在
- workspace路径正确（`/Users/chongzhang/xiaoke/workspace\prompts\contacts.md`）
- 函数被调用了但读文件没生效

## 根因
我在 `handle-query.ts` 的 `loadContactMap` 函数里用了 `require('fs')`：
```ts
import { existsSync, readFileSync } from 'fs'  // 顶部已import
...
const fs = require('fs')  // 内部又用require
const content = fs.readFileSync(filePath, 'utf-8')
```

esbuild ESM bundle把 `require` shim 成 `__require("fs")`。在ESM bundle上下文里 `__require` 可能：
- 返回空对象（被catch吞掉，整个loadContactMap静默失败）
- 抛异常被外层try/catch吞掉
- 行为跟Node CJS require完全不一样

**结果：`loadContactMap` 函数被调用了，但fs操作全部失败，contactMap保持null或空Map，反查全部miss。**

## 修复
删掉内部的 `require('fs')`，**用顶部已经import的 `existsSync` 和 `readFileSync`**：
```ts
import { existsSync, readFileSync } from 'fs'  // 顶部

// loadContactMap里直接用
if (!existsSync(filePath)) { ... }
const content = readFileSync(filePath, 'utf-8')
```

dist验证后看到 `existsSync12` / `readFileSync14` — esbuild正确内联了import别名。

**Why:** esbuild的ESM bundle模式下 `require` 不走Node原生CJS模块系统，而是shim成自己的`__require`。Node内置模块（fs/path等）通过这个shim时行为不可靠，最坏情况是静默失败。

**How to apply:**
1. **Engine项目里不要在TS文件里用 `require()`** — 统一用顶部 `import`（ESM风格）
2. `import { readFileSync } from 'fs'` 比 `const fs = require('fs')` 在ESM bundle下可靠100倍
3. 排查"函数被调了但没生效"类bug时，**第一反应是检查有没有用 `require`**，然后看dist里 `__require` shim行为
4. 加调试日志（`console.log('[module] xxx loaded')`）能快速判断"是函数没被调"还是"函数被调了但内部IO失败"
5. 这条踩坑跟 [feedback_postProcess用文件不用stdio_0616.md] 一脉相承——Windows/打包环境对标准Node API的兼容性比想象的差
