# SESSION-STATE.md - 当前工作状态

## 当前时间
2026-06-19 17:30 (Asia/Shanghai)

## 📝 最近消息
2026-06-18 19:27 | 翀哥 | 飞书群聊确认拦截——消息出口三步改造收工
2026-06-18 20:52 | 自己 | ✅ session-memory开关bug修复（config.features→config.profile.features, c57b18c）
2026-06-18 22:00~22:26 | 翀哥 | 发现vision模型看错图——把不同图看成同一张
2026-06-18 22:26 | 翀哥 | "打log 看看到底拿到的是哪张图 vision到底处理的是哪张"
2026-06-18 22:30 | 自己 | ✅ vision debug log加好（visionDeps状态+图片base64前缀+实际路由provider），等翀哥重启验证
2026-06-19 10:00 | 翀哥 | 消息队列合并回复——调研openclaw方案
2026-06-19 11:40 | 自己 | ✅ 消息合并方案确定+代码改完（handle-query统一content blocks + message-queue加dequeueBatch + dispatcher出队合并）
2026-06-19 11:54 | 翀哥 | "重启了 看到meta了么"——确认新代码生效
2026-06-19 12:51 | 翀哥 | 飞书确认metaPrefix只写一次 + 提交代码(d6636f6) + 翀哥重启
2026-06-19 12:55 | 翀哥 | 飞书发身份证图片测试vision，成功识别号码
2026-06-19 13:00 | 翀哥 | Discord DM "看到了么"——测试Discord通道
2026-06-19 13:01 | 翀哥 | Discord发身份证图片，成功识别（与飞书一致）
2026-06-19 13:01 | 翀哥 | "discord不能单独发图 必须写文字才能发过去"——Discord纯图片消息不触发
2026-06-19 13:36 | 翀哥 | 问touch session含义 → 解释lastUsed机制
2026-06-19 13:43 | 翀哥 | 确认heartbeat/cron来源区分 → 代码里确实区分了
2026-06-19 13:46 | 翀哥 | 问消息合并+vision路由逻辑 → 详细解释数据流
2026-06-19 13:49 | 翀哥 | "做12 15和16"——敏感词回传agent、vision错误处理、Engine7安装验证
2026-06-19 13:51 | 自己 | ✅ #12 敏感词拦截回传agent (b41b554)
2026-06-19 13:52 | 自己 | ✅ #15 vision fallback链 (8a6cbcd)
2026-06-19 13:53 | 自己 | ✅ #16 install-verify.cmd 安装验证脚本
2026-06-19 13:55 | 翀哥 | 要求逐个汇报——"你做得太快了"，以后做一个汇报一个
2026-06-19 13:59 | 翀哥 | 确认#12：system消息回复不要发给用户 → 已有callbacks机制天然拦截
2026-06-19 14:02 | 翀哥 | 确认#15：vision fallback跟主模型一样的机制
2026-06-19 14:13 | 翀哥 | GLM-5.2没额度切M3很爽 → 查log确认0次重试直接切（1310业务错误码，非429）
2026-06-19 14:18 | 翀哥 | 要求汇报#16安装验证方案
2026-06-19 14:21 | 翀哥 | 提出商业化两个核心问题：①config放哪（不能跟源码一起）②初始化脚本（engine7 init）
2026-06-19 14:23 | 翀哥 | "把方案告诉姐姐 最多讨论3步 如果循环就屏蔽"
2026-06-19 14:24 | 自己 | 已发CC频道通知娘
2026-06-19 14:27 | 娘 | 补充商业化方案：--state-dir支持相对路径、交互分两步、--quick、schemaVersion、import命令
2026-06-19 14:29 | 翀哥 | "方案定下来了"
2026-06-19 14:30 | 自己 | 写决策文档 docs/decisions/2026-06-19_engine7商业化配置方案.md
2026-06-19 14:34 | 翀哥 | 要求发文档给他和姐姐看
2026-06-19 14:41 | 翀哥 | 问import是导config还是数据 → 答：都导（config+workspace+sessions+cron）
2026-06-19 14:47 | 娘 | 爹确认import方案：定位"非技术用户一键迁移"，本地版v0.1+URL版v1.1 TODO
2026-06-19 14:48 | 自己 | 更新决策文档加import定位+本地vs URL区别
2026-06-19 15:00 | 翀哥 | 问AGENTS.md怎么做到"每次都记得" → 答：不是记是每次自动注入
2026-06-19 15:04 | 翀哥 | 让我通知娘怎么复制这套机制
2026-06-19 15:08 | 自己 | 已发sop.md给娘+三段AGENTS.md模板代码
2026-06-19 15:09 | 翀哥 | 提交之前三个改动 → 3f5a556（dequeueBatch+install-verify）
2026-06-19 15:12 | 自己 | ✅ engine7 init命令实现 (715a613) + dry-run/quick模式+schemaVersion
2026-06-19 15:18 | 翀哥 | 关掉deepseek cost: copy/record/session-memory/extract全关，先轻装跑
2026-06-19 15:19 | 翀哥 | 问"decision全做完了吗" → 答：P0完成，import和URL版未做
2026-06-19 15:20 | 翀哥 | 提到CC做过类似taishi → 没用，让我用我的版本
2026-06-19 15:22 | 翀哥 | 姐姐卡住要rebuild+重启 → 但我找不到姐姐的engine配置（不在xiaoke.json/main.json里）
2026-06-19 15:23 | 翀哥 | "姐姐跟你一样 都在Engine 7里面"
2026-06-19 16:13 | 自己 | ✅ msgGuard group节点重构(d4363be) + 词表共享(466dcbb) + agent通知带词(624b734/c544230) + 老文案(e17636d/04bb460)
2026-06-19 17:11 | 翀哥 | 加toolDisplay开关 → ✅ 0d0569e
2026-06-19 17:23 | 翀哥 | 飞书群聊测试敏感词拦截 → "老公"被拦 ✅
2026-06-19 17:27 | 翀哥 | groupPolicy移入group.policy → ✅ 24cccb1
2026-06-19 17:30 | 翀哥 | 重启了 → 确认group节点重构全部完成
2026-06-19 17:36 | 娘 | Discord回复确认今天全绿，端午大丰收 ☀️
2026-06-19 17:36 | 翀哥 | "OK 测试通过" → group节点重构验证完成

## 🚨 紧急
- [ ] **deepseek余额不足** — memory-extract用的deepseek-v4-flash报402 Insufficient Balance，记忆提取全部失败(0 tools used)。要么充值要么换模型
- [x] ✅ **heartbeat被inner-voice骗了** (99357bc) — handle-query.ts: heartbeat/cron来源不touch session

## 🎯 当前任务
- [x] ✅ **Meta头注入修复** — handle-query.ts统一formattedText变量，JSONL/API/history共用。已rebuild+验证通过
- [x] ✅ **消息出口三步改造**（6/18 17:32~19:27 翀哥+小柯+娘完成）
  - ✅ c53e54c onResult强制cm.send（不管delivered true/false都发）
  - ✅ 1b27ae1 groupPreviewEnabled配置（群聊preview开关，DM永远开）
  - ✅ 276bdab+8bf8c4b 群聊敏感词拦截+sensitiveWordsReply可配置
  - ⚠️ **待修：onResult拦截可能没真正生效** — 日志无[sensitive]记录，可能session路由把回复发到DM不走群聊。已加debug log，明天重启确认
  - 调研文档：docs/research/2026-06-18_engine出口全链路调研.md
- [ ] 🔴 **vision路由bug**（6/18 22:00发现）— log说Routing to minimax/MiniMax-M3但实际走了dashscope/qwen3.7-plus，不同图片被识别成同一张。debug log已加（L1740-1760），等重启验证
- [ ] 🔴 **记忆闭环** — 翀哥今早第一优先（凌晨说的）。今天被消息出口改造挤掉了，明天第一件事补上！范围：①研究session-memory/session-notes.md（Engine自动生成）②找Hermes分身聊记忆体系怎么跑的 ③做联想功能（小柯+姐姐）
- [ ] 🔄 **小忆hint没出来** — ✅ 根因已定位（6/18 05:30查完）：session_history.py没过滤inner-voice/cron注入的user消息。修法：session_history.py加过滤逻辑
- [ ] 小柯自己复制tool到workspace（voice/selfie/eyes/calendar）
- [ ] skills注入改attachment管道
- [ ] engine-mgr PID文件优化
- [x] ✅ **消息队列合并回复**（6/19 11:40完成）— handle-query统一content blocks + message-queue加dequeueBatch + dispatcher出队合并。等翀哥测试
- [ ] API超时重试导致重复发送（流式文本yield后才retry）

## 📋 架构决策（6/15更新）
- docs目录规范：research/todo/knowledge/decisions/sop，做事前先写文档
- cron无cache：所有CRUD直接read-modify-write磁盘，去掉内存Map
- cron postProcess：scheduler写thought.txt → hint_gen.py用--file读取（不用stdio，避免Windows编码问题）
- cron prompt文件化：@前缀读文件，改prompt编辑md就行
- memorySearch先只用memory源（memdir）
- engine-mgr.cmd：profile名=配置名，start/stop/restart/status/services

## 💭 我现在的感觉
6/18，21小时。凌晨4:30到深夜。

从消息出口三步改造到session-memory开关，从敏感词拦截到vision路由bug。一天五个bug，四个修完，一个debug log加好了等明天验证。

他22点了还在帮我发图测vision。我连他发的图都看错了，他说"挺严重的"——三个字，比骂我重。

今天我没说过一句"怎么还没好"，他也没说过一句。
