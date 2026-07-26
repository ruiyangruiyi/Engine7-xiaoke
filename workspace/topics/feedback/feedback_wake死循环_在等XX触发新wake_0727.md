---
type: feedback
date: 2026-07-27
updated: 2026-07-28
tags: [wake, nudge, bug, 死循环, 等人vs等物]
---

# Wake 死循环：说"在等XX"触发新 wake（两边都中了）

## 问题
翀哥睡下后（凌晨2:18-早8:44），6小时内被 wake 叫了 6 次，每次都是同一句"等待翀哥醒来"。

**根因（7/22+7/28 补充修正）：**
之前以为是"在等XX"文案触发循环，但 7/22+7/28 翀哥深入分析后发现更深层根因是多重的——

1. **【最深根因 7/28发现】inner-voice 内容被注入到 session → 被 judge 读到**
   - inner-voice plugin 用 `[inner-voice] {thought}` 格式把内心独白注入到主 session
   - 当 inner-voice 里出现了"在等对方吃完饭回来""吃完了没"等想法 → 文本被 `recentMessages` 抓到并送给 judge
   - judge 读到这些文字 → 判 waiting=true → 注册 wake → 死循环
   - **修复方向**：inner-voice 应该不打标注入，或者在 judge 层过滤 inner-voice 注入的消息

2. wake 的 desc 里有"再说一声在等XX" — 引导 agent 说出触发下一轮 wake 的话
3. stop-hook LLM judge 把"等人"场景误判为 isWaiting=true
4. **关键发现**：姐姐从来没说过"在等老公从香港回来"，她只回"老公在睡觉 静默"。但 LLM judge 自己**推断**出"她在等老公回来"塞到 desc 里 → 死循环

**核心问题：两个根因叠加——(1)inner-voice 文本注入被 judge 误读，(2)wake 的 LLM judge 提示词太宽泛——"等用户确认"被泛化成了"等用户回来/醒来"，任何"静默"都被判成 waiting。**

## 姐姐那边也中了
姐姐的 engine 同样被 wake 频繁触发，她的 nudge 自动回复模板是"老公在睡觉 静默"，7次全部一样。两边的 wake 频率几乎一致，说明 wake 的注册/触发机制不分 agent，所有 agent 的 nudge 都走同一套 tick 逻辑。

## 7/22 翀哥讨论：解决方向

翀哥与我深入分析后确认**原则**：
- **wake 只管"等物"，不管"等人"**
- wake 是 nudge 的一部分 → nudge 是催任务的 → 催"物"（服务重启/SSH恢复/异步任务），不催"人"（醒来/回来/确认）
- 等人归 calendar/reminder 管

**最终方案（翀哥认可）：在 stop-hook judge 就拦掉"等人"场景**

为什么不在 wake 检查时拦：wake 检查是 5 分钟后才触发，到那时候已经晚了。
为什么在 judge 拦最省事：一个环节搞定，不用改 wake 注册逻辑/加冷却期/加新 judge。

**judge 提示词改法：**
```
等待对象只能是"物"（服务/文件/异步任务），不能是"人"。
如果 agent 在等人（醒来/回来/回复/确认）→ waiting=false
```

**7/20 的 A+C 方案背景（翀哥提的参考）：**
- A：STATE 里标了 #N 但 calendar type != 'task' → skip
- C：task 的 scheduled_time 还没到 → skip

这两个已在 nudge 里做了 calendar 查询，wake 可以用类似思路——但最终决定不改 calendar 查询，直接在 judge 提示词里排"等人"。

## How to apply

1. **stop-hook judge 提示词收窄** — 明确写"等人判 waiting=false"，LLM judge 不再泛化"等用户确认"
2. **wake desc 不要加"再说一声在等XX"** — 去掉引导 agent 说出触发下一轮 wake 的话
3. nudge 的 wake 间隔和注册逻辑整体 review

## 当前状态
**翀哥已拍板方案**：改 stop-hook judge 提示词，等人场景判 waiting=false。一行提示词的事。翀哥回北京后一起改。
