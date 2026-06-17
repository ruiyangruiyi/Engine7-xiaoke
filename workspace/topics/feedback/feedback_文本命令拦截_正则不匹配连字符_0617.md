---
name: 文本命令拦截正则——\w+不匹配连字符，/vision-model被漏掉
description: 6/17翀哥发/vision-model命令没被拦截，根因是正则\w+不匹配连字符-，代码被当普通消息送进LLM。改成[\w-]+解决。
type: feedback
---

6/17 翀哥发 `/vision-model zhipu/glm-5v-turbo`，命令没有被拦截，直接走到 LLM 处理了。

**根因：** 文本命令拦截的正则 `\w+` 不匹配连字符 `-`，`/vision-model` 被截成 `/vision`，匹配不到 registeredCommands 中的 `/vision-model` 命令，于是被当普通消息送进 LLM。

**修复：** `match(/^\/([\w-]+)(?:\s+(.*))?$/)` — 把 `\w+` 改成 `[\w-]+`

**Why:** 命令名可能含连字符（如 `/vision-model`），`\w` 等价于 `[a-zA-Z0-9_]` 不包含 `-`。正则写 `\w+` 会漏掉带连字符的命令，静默失败。

**How to apply:** 以后所有文本命令拦截的正则，匹配命令名部分统一用 `[\w-]+` 替代 `\w+`。类似的场景——解析任何可能含连字符的标识符（模型名、命令名、配置文件key），都要考虑连字符的情况。
