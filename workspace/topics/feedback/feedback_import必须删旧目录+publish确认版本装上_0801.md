---
name: import前必须删旧目录 + publish后必须确认版本
description: 2026-08-01 #129 翀哥"重新import好像没有了"——import不清理旧文件，engine启动后session-index会被新session覆盖；publish后npm install可能因registry延迟静默失败，必须确认版本装上
type: feedback
date: 2026-08-01
---
# import 前必须删旧目录 + publish 后必须确认版本

## 事实
8/1 #129 7.1.18 → 7.1.19 连续两版踩同一个坑：

**坑 1：import 不会清理旧文件**
- 翀哥 15:44 反馈："你确定都改了么，我都没看到原来的jsonl文件覆盖过去"+"刚才找到了是mac上的就2条消息"+ 删了 xiaoke 目录后 "重新 import 好像没有了"
- 根因：Mac engine 启动后会用 `session-index.json` 写新映射（starting fresh），新生成的 jsonl（`d1f70137`、`2651463b`）覆盖了刚 import 进去的旧文件
- **import 是"增量覆盖"，不是"全量替换"**——新 engine 启动会往旧 index 里追加新条目，旧数据看似没动但被新会话覆盖

**坑 2：npm publish 后 install 静默失败**
- 我 16:10 说 "Mac 上用的不是 7.1.19，export 是用 7.1.18 跑的"
- 根因：npm registry 同步有延迟，`npm install -g engine7@7.1.19` 没报错但实际装的是上一个版本
- 我之前没核对"npm install 到底装上了没"——翀哥最后告诉我"是7.1.19只是我没删xiaoke目录"，但**前提是他已经自己确认过版本**

**Why:** travel 流程里 import 是"恢复 agent 状态"的关键步骤，旧状态残留会让"刚导入的恢复"被新启动覆盖；而 publish→install 链路任何一环延迟/缓存都会导致用户用的不是最新版本——我之前的脚本都假设"npm publish 完了立刻可用"。

**How to apply:**
- **import 前永远提醒"删旧目录"**：在 travel/import 类指令里，第一条命令永远是 `rm -rf <stateDir>`，不是"建议"而是"必须"
- **publish 后必须验证**：`npm view engine7 version` 看 registry 上的最新版本号，再让用户 `npm install -g engine7@<版本号>` 指定版本而不是 `@latest`
- **不要相信 silent success**：任何 `npm install` 之后必须 `engine7 --version` 或 `which engine7` 确认装上的版本对得上要 publish 的版本
- **import 是覆盖不是替换**：跨机器/跨环境恢复场景，先彻底清空目标目录再 import，不要依赖 import 的覆盖逻辑