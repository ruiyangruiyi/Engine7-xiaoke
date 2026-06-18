# Working Buffer — 2026-06-18 03:37

## 正在做什么

凌晨跟翀哥修 meta 头注入 bug + 配 GLM-5.2 + 重构 handle-query.ts。全部完成。

## 今晚做了什么

1. ✅ **Meta头注入修复** — formatWithMeta 之前只在 writeUserMessage（写 JSONL）调，没传给 API 和 history。翀哥测了一晚上没生效，根因：我改了 src 没 rebuild dist
2. ✅ **新 meta 格式** — 从 `[meta: HH:MM/来源@ID (name)]` 改成 `name (ID) @来源#频道   HH:MM:SS`，人名在前
3. ✅ **GLM-5.2 配置** — 三个 config 全加，小柯+姐姐切 primary，testengine 不切做对比。contextWindow=1M, maxTokens=128K
4. ✅ **start.cmd 杀自己进程 bug** — powershell kill 命令匹配到自身命令行，加 `$_.Name -eq 'node.exe'` 修复
5. ✅ **handle-query.ts 重构** — 翀哥指出：format 一次，JSONL/API/history 共用一个 formattedText 变量，保证绝对一致

## 翀哥今晚的关键反馈

- "测了一个晚上 真的就没有过 都是幻觉" — 我改 src 没 rebuild dist
- "我还不断提示你 要看src 别老盯着dist" 
- "你记住啥了 你都不记 下次重启还有个屁" — 必须写记忆文件
- "严谨点哦"
- 重构思路：writejsonl 的内容和写进 API 的内容（存入 history 的）应该一致，开始 format 好弄一个变量传两处

## Git 提交

- `1ddc255` — meta注入修复+GLM-5.2配置
- `1d9d004` — start.cmd杀自己进程fix
- `4a14aeb` — formatWithMeta统一formattedText变量

## 下一步

- 翀哥说 5.2 有点慢，看白天表现再决定要不要切回 5.1
- 记忆闭环任务还没做（被今天 meta 修复挤掉了）
