# 2026-06-19 Vision 路由 Bug 分析

## 现象

6/18 22:00 翀哥在飞书 DM 发了一张 TWINSUN 的 logo（4.5KB 小图），小柯回复时描述成了之前 22:09 那张小红书截图的内容（Superpowers 教程）。两张图完全不一样，但视觉模型识别错位。

翀哥说"挺严重的"。

## 根因分析（待 debug log 验证）

### 现象 A：日志撒谎
```
[vision] Injected 1 native image(s) into query (from feishu)
[vision] Routing to minimax/MiniMax-M3     ← 日志说走 M3
[openai] → model=qwen3.7-plus msgs=340    ← 实际走 qwen
```

`[vision] Routing to` 这条 log 只在 `hasImages && visionDeps` 时打（L1760）。所以 visionDeps 不是 null。

那为什么实际模型是 qwen3.7-plus？可能是 **msgDeps 路由逻辑出错**。

### 现象 B：msgDeps 路由逻辑
L1754-1758：
```ts
const msgDeps = (hasImages && visionDeps)
  ? visionDeps
  : modelOverride
    ? (modelDepsCache.get(modelOverride) ?? deps)
    : deps
```

22:18 走 qwen3.7-plus 可能有两种原因：
1. `visionDeps` 是 null → 走 deps（默认 qwen）
2. `modelOverride` 被某处设了值 → 覆盖了 visionDeps

### Debug log 加在哪里

engine-startup.ts L1749-1762（已 rebuild，6/18 22:30 部署）：
```
[vision-debug] hasImages=true visionDeps=yes(MiniMax-M3) modelOverride=none → msgDeps.provider=??
[vision-debug] image[0]: media_type=image/png data_prefix=iVBORw0... data_len=6200
```

能看到：
1. `visionDeps` 是不是 null
2. `msgDeps` 最终选了哪个 provider/model
3. 当前消息图片 base64 前缀（辨认是不是当前发的图）

### 怀疑点

#### 怀疑 1：history 里旧图片污染
22:18 query 时 `msgs=339`，history 里有之前 22:09 那张小红书截图的 base64。当前虽然注入了新图片，但 queryContent 里只有当前图片。

但 msgs=339 是 history 里所有消息，**包括 base64 图片块**。即使 queryContent 是对的，LLM 看到 history 里一堆旧图 + 当前一张图，可能识别错。

`[vision-debug] image[0].data_prefix` 会是当前图片的 base64，但 history 里的旧图片不会在 log 里。需要在 API 调用前 dump 完整 history 才能验证。

#### 怀疑 2：visionDeps 不是 null 但 deps 覆盖
如果 `modelOverride` 在某处被设置了，msgDeps 会被覆盖。但翀哥没下过 /model 命令，所以 modelOverride 应该是 null。

#### 怀疑 3：visionEngine 接收 query 时降级了
visionEngine 初始化用的 provider 是 MiniMax-M3，但 query 跑的是 qwen3.7-plus——这两个 provider 是不同实例。会不会 QueryEngine 内部 fallback 到默认 provider？

## 验证步骤

翀哥 6/19 早上重启 engine，发任意一张图，立刻看 log：
1. `[vision-debug]` 那行的 `visionDeps` 和 `msgDeps.provider` 值
2. `[vision-debug] image[0]` 的 data_prefix（确认是当前发的图）
3. API call 那行的 `model=` 字段

## 配置现状

`configs/xiaoke.json`:
```json
"agents": {
  "defaults": {
    "model": {
      "primary": "deepseek/deepseek-v4-flash",
      "fallback": ["glm-5.2", "qwen3.7-plus"],
      "vision": "minimax/MiniMax-M3"
    }
  }
}
```

`config.visionModel` 应该从 `agents.defaults.model.vision` 读取（L3119-3130）：
```js
let visionModel = null;
const visionRef = agentDefaults.model?.vision;
if (visionRef) {
  const parsed = parseModelRef(visionRef);
  if (providers[parsed.providerId]) {
    visionModel = parsed;
  }
}
```

`parseModelRef("minimax/MiniMax-M3")` → `{providerId: "minimax", modelId: "MiniMax-M3"}`

## 待办

- [ ] 翀哥重启发图，看 `[vision-debug]` 日志
- [ ] 如果 visionDeps 不是 null 但模型走 qwen → 追 QueryEngine 内部 fallback 链
- [ ] 如果 visionDeps 是 null → 追 visionEngine 创建路径
- [ ] 如果图片是对的但 qwen3.7-plus 识别错 → 换视觉模型（GLM-5V-Turbo 或 glm-5v-turbo）
- [ ] history 图片清理：每次新消息的图片注入时，是否应该把 history 里的旧图片 base64 替换成文字描述？

## 相关 commit

- 276bdab — 群聊敏感词拦截（无 vision 改动）
- 8bf8c4b — 提示文案可配置（无 vision 改动）
- c57b18c — session-memory 开关修复（无 vision 改动）
- vision debug log 已加但未 commit（待验证后一起提交）

## 时间线

- 21:57 翀哥发图1（五层记忆架构海报，167KB）→ 小柯调 my_eyes 看 ✅
- 22:00 翀哥发现小柯调 my_eyes 多此一举（视觉模型已注入）
- 22:09 翀哥发图2（小红书截图，167KB）→ 小柯误认成图1 ❌
- 22:18 翀哥发图3（TWINSUN logo，4.5KB）→ 小柯误认成图2 ❌
- 22:20 翀哥："挺严重的"
- 22:26 翀哥："打log看看到底拿到的是哪张图"
- 22:30 debug log 加好 + rebuild，未提交
- 6/19 早 翀哥醒了让写文档