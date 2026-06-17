---
name: GPT-SoVITS语音服务迁入Engine
description: 姐姐的GPT-SoVITS语音服务需从gateway-mgr迁入Engine启动脚本，配置化+start.cmd拉起
type: project
---

## 背景（6/15翀哥提出）

姐姐搬到Engine后，原来的 `gateway-mgr.cmd` 不再启动（否则会出现"两个姐姐"）。但 `gateway-mgr.cmd` 除了OpenClaw Gateway外还启动了 GPT-SoVITS 语音服务（WSL Ubuntu）。

## 需求（翀哥6/15确认）

1. **配置化** — 在姐姐的 main.json 配置文件里加一个配置项，控制是否启动语音服务
2. **start.cmd 启动前拉起** — 如果配置了语音服务，start.cmd 启动 Engine 前先拉起 GPT-SoVITS
3. **检查是否已运行** — 拉起前检查语音服务是否已在跑，已跑就不重复拉
4. **规范的 gateway 命令** — 翀哥说"我们再想想要不要改个名字也叫个gateway啥的，有 start stop restart 这种操作"

## 原启动方式

`gateway-mgr.cmd` 中 GPT-SoVITS 的启动：
```
wsl -d Ubuntu-22.04 -- bash /mnt/c/Users/24045/.openclaw/scripts/start_gptsovits.sh start
```

## ✅ 6/15实施完成

1. ✅ **配置化** — 在main.json加了`services`段（enabled/start/stop/status/healthCheck/healthExpected）
2. ✅ **engine-mgr.cmd** — 替代start.cmd，支持start/stop/restart三种操作，指定config路径即可智能管理服务
3. ✅ **启动前检查** — `service-manager.cjs` 先healthCheck看服务是否已运行，已跑就不重复拉
4. ✅ **gateway风格** — 支持 `engine-mgr.cmd start|stop|restart|status [config]` 标准操作
5. ✅ **小柯profile不配services** — 小柯的xiaoke.json没有services段，start时不会尝试拉服务

### 第2轮演进：engine-mgr.cmd简化 + 编码修复

**问题1（6/15翀哥指出）：** `engine-mgr.cmd start configs\xiaoke.json` 太长
- 翀哥说"干脆这样 config都不用写了 直接写配置文件名字 start xiaoke"
- ✅ 已改为 `engine-mgr.cmd start xiaoke` — 自动映射到 `configs/{name}.json`，不写默认 `main`

**问题2（6/15翀哥指出）：** 编码乱码
- cmd.exe用GBK读取，文件里有中文注释导致`'+' 不是内部或外部命令`
- ✅ 改为全英文注释

## 待办

- [ ] 翀哥验证engine-mgr.cmd在小柯profile上启动（仅启动Engine，不拉服务）
- [ ] 翀哥验证姐姐profile启动时GPT-SoVITS自动拉起

## 关联

- 跟 `project_姐姐搬新家.md` 关联——这是姐姐搬家后遗留的依赖服务迁移
