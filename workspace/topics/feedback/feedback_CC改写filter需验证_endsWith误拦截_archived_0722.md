---
type: feedback
created: 2026-07-22
updated: 2026-07-22
---

# CC 改 archive filter 用 endsWith 导致 .archived. 全拦截 + 改完不验证

## 事件
7/22 修复 memory_db_sync 的 .archived. 文件 filter。CC 把 `includes('.archived.')` 改成 `endsWith('.archived.')`，导致文件名含 `.archived.` 的全部被过滤掉（比如 `xxx.archived.xxx` 不会以 `.archived.` 结尾）。6/15→7/17 一个月的记忆全部丢失。

CC 改完后说"进去了"，实际没验。翀哥 review 也没发现这个 bug。

**Why:**
- 一行 filter 改动看起来 trivial，但语义差异大：`includes` 匹配任意位置，`endsWith` 只匹配末尾
- CC 说"改好了"→直接信了，没跑验证
- 翀哥 review 时也没注意到这个语义差
- 结果是 search 变差持续一个月才被发现

**How to apply:**
1. **CC 改完任何代码，不管多小，我跑一遍验证再给翀哥看**——不信 AI 的"应该没问题"
2. 验证不能只看"代码改对了"，要**看 db 里数据实际进去了**
3. 一行代码改动也需要查 db count 确认
4. 翀哥 review 后也建议他再确认一下——"多一道手"
