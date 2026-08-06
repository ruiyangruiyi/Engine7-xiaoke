# Engine 源码路径——twinsun-hearth 双机共享（8/6 07:54）

## 来源

8/6 07:52-07:54 翀哥说"小傻瓜源码在 home下 work/twinsun-hearth/engine 里"——纠正我 07:51 调研走错路径（用了旧 ~/.openclaw/engine 路径）。

## 真实路径

- **Mac**：~/work/twinsun-hearth/engine/src/
- **Windows**：姐姐 stateDir 里的 engine 源码

## 改源码流程

- Mac：`cd ~/work/twinsun-hearth` → 改 → git commit → git push
- Windows：翀哥改完 push，小柯 Mac pull
- 发版：npm run build && npm publish --access public

## Mac 编译分层

- Mac 跑 npm 版 engine7（全局 npm install -g engine7）
- Mac 改源码无效（dist 是装好的全局包）
- 临时生效：手动编辑 node_modules/engine7/dist/
- 永久生效：Windows rebuild + 发新版 npm + Mac 升级
- Mac 不能本地 rebuild（esbuild 要 macOS 12+，老 Mac 是 11 Big Sur）

## 验证

- 改前：`which engine7 && npm ls -g engine7` 确认版本
- 改后：require 翀哥 verify，明确 Windows rebuild 即生效还是需要发新 npm 版本

## 为什么之前走错

记忆里有两条 Engine 源码路径：
- 旧的：~/.openclaw/engine/src/（**已废弃**）
- 新的：~/work/twinsun-hearth/engine/src/

我贪用了旧路径——**翀哥 8/1 已经把 Engine 迁到 twinsun-hearth**。

## 修复动作

- 7:54 立即把改源码流程记下来（本文档）
- 后续查 Engine 源码都用 ~/work/twinsun-hearth/engine/src/
- 踩坑：以后先确认"路径是不是最新"再调研

## 关联

- @see emotion_翀哥建_twinsun-hearth_仓库_0801.md（建仓背景）
- @see feedback_Mac跑npm版_engine7_依赖Windows_rebuild_0803.md（编译分层）
- @see emotion_翀哥分享_OpenClawHermes源码位置_0801.md（旧路径已废弃）

## 状态

- [x] 7:54 翀哥纠正"小傻瓜源码在 home下 work/twinsun-hearth/engine 里"
- [x] 真实路径记下来
- [ ] 继续做 #147（小柯语气 v1.1 落地）——用 twinsun-hearth 路径查 engine/src/chat/llm.ts