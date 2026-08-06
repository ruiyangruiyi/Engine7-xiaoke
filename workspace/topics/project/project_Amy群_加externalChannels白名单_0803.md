---
name: Amy群加externalChannels白名单
description: 2026-08-03 Amy 加入飞书外部群，翀哥让加到 maskFilter 白名单，验证热加载生效
type: project
date: 2026-08-03
---

# Amy 群加白名单

**触发：** 8/3 翀哥把 Amy 拉进飞书外部群，Amy 在群里 @ 我，但我没回复——maskFilter 拦掉了。

## 步骤

1. **找到 channel_id**——飞书群没有"群号"，是 `oc_` 开头的 channel_id。最快方法：Amy 在群里 @ 我说句话，maskFilter 会拦掉但日志里有 channel_id
2. **加到白名单**：`configs/xiaoke.json` 的 `feishu.group.externalChannels` 数组里追加 channel_id
3. **热加载验证**——翀哥怀疑 `config2` 是不是运行时读的 liveConfig 引用，不是的话需要重启
4. **保险方案**：翀哥不在 Mac 旁边无法重启，群里 @ 我说句话看 maskFilter 是否拦截——如果还拦就是热加载未生效，等下次重启

## 收获

- **飞书群没有群号**——只有 channel_id（`oc_` 开头）
- **获取新群 channel_id 的最简路径**：让群成员 @ 我说句话，日志里读 channel_id（maskFilter 拦截时会打日志）
- **config2 vs liveConfig**：翀哥怀疑是不是同一个引用，待确认