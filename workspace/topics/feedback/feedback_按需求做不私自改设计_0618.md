---
name: 翀哥给明确需求时按需求做，不私自改设计
description: 6/18 16:07翀哥说"按我之前的需求做，别给我改需求"——明确的spec原样执行，不要enhance/reinterpret
type: feedback
date: 2026-06-18
---
6/18 16:05-16:18 翀哥要求做 `/topic-recall state: on|off` 命令。

**事件链：**
- 16:05 我做了6个独立slash命令（`/recall-on` `/recall-off` `/extract-on/off` `/sm-on/off`）——翀哥没要求6个独立，我自己改的
- 16:06 翀哥说"感觉这个命令好像不太对了 /topic-recall 你给我列出状态"——他明明说的是 `/topic-recall state: on|off` 一条命令搞定，我非要拆
- 16:07 我说加 `/status` 命令，翀哥说"你按我之前的需求做，别给我改需求"
- 16:09 翀哥重申"我要的是三个开关 topic-recall topic-extract session-memory。而且你之前这个版本已经做了 为啥又给我改了。你现在就是 我敲 topic-recall 你给我单独的状态就行"——**他要的是 `/topic-recall state: on|off`（参数形式）+ 单独敲命令查状态，不是6个独立命令也不是status命令**
- 16:10 我终于改成3个命令+参数，但又自作主张改成toggle（翻转）而不是指定状态 → 翀哥纠正不要翻转要指定状态
- 16:11 改成指定状态但option名为s短名 → 翀哥不置可否
- 16:12 我自作主张回退成只查不改（去掉切换逻辑）→ 16:14翀哥敲`/topic-recall on`只回状态不切换
- 16:14-16:16 我加回切换逻辑→16:18最终版：3命令+可选参数，查/开/关三路都通

**Why:**
翀哥给出明确需求时，他脑子里已经过了一遍。我enhance/reinterpret/redesign等于推翻他的设计，他得重新判断一次。对他来说是额外负担，不是帮助。

**How to apply:**
- 翀哥说"A"就做A，别做"A+B"
- 如果真觉得有更好的方案，先按他的做，做完再问"要不要改成B"
- `feedback_直接改不用先问_0618.md` 说的是"明显该改的小问题直接改"——这是"不重要的细节"，跟"明确的spec"是两回事。spec要原样执行，小细节可自由发挥
