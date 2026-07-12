---
name: 别过度修，听翀哥的
description: 2026-06-22 修 429 fallback 死循环时被翀哥批评"过度改了"
type: feedback
---

# 别过度修，听翀哥的

## 背景
2026-06-22 修 429 fallback 死循环，过程中犯的错。

## 教训
1. **不要被用户的"纠正"带偏**——翀哥两次纠正都是真根因，但我继续往下挖到了不该挖的地方
2. **注释 ≠ bug**——fallback-provider 注释说 5min 但代码 24h，**可能是设计**（24h 是"必须手动 /model 恢复"），不是 bug
3. **每多改一处 = 多一处风险**——每次 commit 都要想"这是真根因吗？还是我以为的根因？"
4. **验证后再改**——先用证据说话，不要"我觉得"

## 时间线
- 09:35 我猜根因：fallback 递归无深度限制
- 09:46 翀哥纠正：死循环不是切多个 model，是同一个 glm-5.2 一直 probe
- 09:53 我又猜：cooldown 24h 太长 + probe 无间隔 → 改了 `15109db`
- 10:08 翀哥再纠正：model 之前已经 stop 了，stop 没起作用
- 10:16 翀哥批评：cooldown 24h 可能是设计，**别来回试着玩**

## 真根因（最终）
- **`/stop` 用 `(modelOverrideEngine ?? engine)` 瞎猜 engine interrupt** — 猜错时 abort 没发到当前 in-flight query
- 修法：`runningEngines` 跟踪 sid → 实际跑的 engine

## 我不该改的
- `15109db` 改的 cooldown 5min + probe 退避 30s → **过度改**，已 revert (`c1a9f5f`)
- 翀哥说"现在的挺好的"——意思是 fallback 默认行为没问题，根因不在那

## 反思
- 我在 root cause 没确认前就开始改代码
- 看到注释和代码不一致就直接当成 bug，没问"为什么这么设计"
- 用户纠正后我没停下来总结"还有没有别的可能"，而是继续往下挖

## 补充：ESM vs CJS（11:23 第二次犯）
- 6/22 11:17 修 reload 路径时用了 `__dirname` 直接报错
- 根因：engine 跑的是 `dist/main.mjs`（ESM），`__dirname` 不存在
- ESM 必须用 `import.meta.url` + `fileURLToPath` 算
- **改之前先看 engine 是 CJS 还是 ESM**（`start.cmd` 跑 `node dist/main.mjs` 一眼看出来）

## 11:20 第三次犯：没验证就 commit
- 11:17 commit `a23989c` 改了 reload 路径兼容
- 但我没确认是 ESM 还是 CJS 就用了 `__dirname`
- 该用 `cat dist/main.mjs | head -5` 看 import 风格判断
- "改完觉得对" ≠ "改完验证过对"
- 11:23 报 `__dirname is not defined` → `0f25d10` 改用 fileURLToPath