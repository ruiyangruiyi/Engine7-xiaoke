# TODO: PreQuery / OnResult 改造为 CC 兼容 hook

> 创建：2026-06-24 | 派活：翀哥 21:43 | 待 review：姐姐
> 方案：[docs/decisions/2026-06-24_PreQuery_OnResult改造为CC兼容hook方案.md](../decisions/2026-06-24_PreQuery_OnResult改造为CC兼容hook方案.md)
> 调研：[docs/research/2026-06-24_CC原生hook调研.md](../research/2026-06-24_CC原生hook调研.md)

## 背景

engine 已有 MessageHookRegistry（`hooks/message-hooks.ts`）实现 PreQuery/OnResult 两个进程内回调点位。现在要把它们暴露为 **CC 兼容的 command hook**，让用户能在 config 里配自己的 shell 脚本。

## 前置条件

- [ ] 姐姐 review 方案，确认 4 个决策点
- [ ] 姐姐确认后翀哥批准开工

## 任务清单

### Phase 1: 类型定义（改动小，可独立验证）

- [ ] `hooks/types.ts` — HOOK_EVENTS 加 `PreQuery` 和 `OnResult`；加对应 HookInput 类型
- [ ] `hooks/types.ts` — 加 `PreQueryHookInput` / `OnResultHookInput` 接口
- [ ] `hooks/types.ts` — HookSpecificOutput 加 PreQuery/OnResult 分支

**验证**：`npx tsx --eval` 编译通过

### Phase 2: 执行器（改动中等）

- [ ] `hooks/executor.ts` — 加 `executePreQueryHooks()` 便捷方法
- [ ] `hooks/executor.ts` — 加 `executeOnResultHooks()` 便捷方法
- [ ] `hooks/index.ts` — 导出新方法

**验证**：手动调 executePreQueryHooks，无匹配 hook 时返回空结果

### Phase 3: 主流程接入（改动关键）

- [ ] `engine-startup.ts` — PreQuery 链后（`messageHooks.runPreQuery` 之后）加 `executeHooks('PreQuery')`
- [ ] `engine-startup.ts` — OnResult 链后（`messageHooks.runOnResult` 之后）加 `executeHooks('OnResult')`

**验证**：配一个 echo hook，飞书发消息能看到 stdin JSON

### Phase 4: 端到端测试

- [ ] 写 `hooks/test/echo-prequery.js` — 读 stdin、打印 JSON、exit 0
- [ ] xiaoke.json 配 hooks.PreQuery 指向 echo 脚本
- [ ] 重启 engine，飞书发消息，确认 log 里有 hook 输入
- [ ] 改 echo 返回 `{ continue: false }`，确认消息被拦截
- [ ] 改 echo 返回纯文本，确认消息正常进 LLM

## 四状态说明

```
- [ ]   pending       — 排队，还没开始
- [~]   in_progress   — 正在做 — started M/D HH:MM
- [!]   block         — 卡住，必须带原因+解锁条件
- [x]   completed     — 做完了 — M/D HH:MM→HH:MM (Nmin)
```

## 风险

1. command hook spawn 子进程有 ~50-200ms 开销
2. PreQuery skip 语义——用户脚本返回 continue:false 会阻止进 LLM
3. 进程内 callback 和 command hook 串行执行，callback 先 command 后
