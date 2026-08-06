---
name: Docker build 改完 dist 必须验证——重启后会以为生效但实际还跑旧代码
description: 2026-08-04 12:14-12:50 groupToolDisplay 重启后飞书测试群验证还显示——根因是 build 出三个 dist 只 cp 了 engine-startup.mjs，main.mjs 没换；验证修改是否真生效不能只看代码，要进 dist grep 改动字符串
type: feedback
date: 2026-08-04
---

# build + 替换 + 重启后必须端到端验证——不是看代码，是看 dist + 实测

8/4 上午 12:14 小文帮我重启后，翀哥在飞书测试群 `oc_f5d614d176cca078a029c55f99ae2d4b` 验证 groupToolDisplay——**工具调用还在显示**。我折腾了一中午。

## 排查路径（错的）

1. 看 src 代码——`groupToolDisplay` 判断在 line 2036/2047 都对 ✅
2. 看是不是 StreamPreview / visualEmitter 独立发送
3. 加调试日志到 `dist/engine-startup.mjs`
4. 让小文重启一次
5. 再次验证——还是显示

## 真正的根因

```
$ grep "isExternalGroup" dist/main.mjs
# 0 次！

$ grep "isExternalGroup" dist/engine-startup.mjs
# 有
```

**build 出了三个 dist，我只 cp 了 engine-startup.mjs。** 进程加载的是 main.mjs（入口），它跑的还是旧代码。

build 后挑着 cp 是错的——一个 src 改动可能在多个 dist 里都被 inline 进去，必须全替换 + grep 验证。

## Why

- 跟之前 Mac 上跑 esbuild 不了的根因不同（@see feedback_Mac_esbuild跑不了用手动patch_dist_0804）——那个是 build 链路，这个是 build 后续的部署
- "改了 src + 重启" 给人错觉已经生效了，实际不一定
- 一中午花在排查"代码为什么不生效"上，本质是部署问题

## How to apply

- **Docker build + cp 完 dist 之后**：立刻 `grep <改动字符串> dist/main.mjs` 确认改动在入口 bundle 里
- 验证改动是否生效的**唯一标准**：重启后**端到端实测**（飞书外部群发消息看有没有 🔧），不能只看代码、不能只看进程日志
- 如果只 cp 了 engine-startup.mjs 那种 bundle，**永远要 grep 确认 main.mjs 也换了**
- @see reference_build输出多个dist_必须全替换_main.mjs是入口_0804
- @see reference_Docker_build链_Mac_esbuild跑不了_0804
