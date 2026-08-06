---
name: Engine7 npm 发布规划
description: 2026-07-29 #125 14:00 发布规划完成——Phase 1-4全部通过，engine7@7.0.0 成功上线 npm
type: project
date: 2026-07-29
---

# Engine7 npm 发布规划（#125）

**提出：** 2026-07-29，calendar 14:00 reminder 触发
**文档：** docs/todo/2026-07-29_engine7_npm_publish_plan.md

## 上线记录

- **engine7@7.0.0** 于 2026-07-29 成功发布到 npm
- 15 files, 850KB packed, 3.6MB unpacked
- bin: engine7
- 从 GLM 封号 → CC 伪装 → npm 发布，一个上午全流程打通

## 后续版本
- **engine7@7.1.8** 于 2026-08-01 发布，专门带 travel (export/import) 功能，让 Mac 能 `npm install -g engine7@latest` 后跑 import
- **engine7@7.1.10** 于 2026-08-01 发布，修复跨平台 tar.gz（Windows bsdtar ↔ Mac gunzip）
- **engine7@7.1.11** 于 2026-08-01 发布，export/import 自动带上 `stateDir/configs/`，路径脱敏
- **engine7@7.1.12** 于 2026-08-01 13:50 发布，session 映射文件（platform-map.json + session-index.json）打包+路径重写
- **engine7@7.1.13** 于 2026-08-01 14:00 发布，calendar 白名单(含 `.calendar/`) + archived/compaction 文件收集
- **engine7@7.1.16** 于 2026-08-01 15:30 发布，cron session 清理（只打包主 session 的当前 jsonl + 最近 1 archived），包 47.9MB→45.3MB
- **engine7@7.1.17** 于 2026-08-01 15:15 发布，jsonl 路径脱敏修复（`.jsonl` 加到 TEXT_EXTENSIONS 走 sanitizeContent/restoreContent），修 Mac 上 read `/Users/chongzhang/xiaoke/workspace/...` 报文件不存在
- **engine7@7.1.18** 于 2026-08-01 15:20 发布，JSON 双反斜杠转义修复（`sanitizeContent` 同时匹配 `/Users/chongzhang/xiaoke/` 和 `/Users/chongzhang/xiaoke/` 两种形式），修 session-index.json 路径未替换（Mac 找不到 .jsonl）

## 调研结论

### shims 已全部内联到 bundle

- `setup-runtime-modules.mjs` 已不需要（index.mjs 里 `initRuntime()` 已完整）
- `shims/atob.mjs` 等 shim 文件已内联到 `shims.bundle.mjs`
- dist 目录比想像的干净，但 `package.json` 仍指向不存在的 `dist/shims/setup-runtime-modules.mjs`

### 发现的问题

1. **双 package.json**: `@anthropic-ai/sdk` 编译期依赖锁在 0.37.0，但 bundle 里的实际版本是 0.20.1，不符合预期。
2. **sqlite-vec 系列包**: 8 个包全部 marked external（`sqlite-vec`/`sqlite-vss`/`better-sqlite3` 等），打包时是外部依赖。

### 关键发现：sqlite-vec 跨版本风险

- 编译期 `better-sqlite3@11.7.0` + `sqlite-vec@0.1.6`，但 npm publish 后消费者装的是最新版
- 风险场景：用户 `npm i` 时装到 `better-sqlite3@12.x` + `sqlite-vec@0.2.x` → C API 不兼容 crash
- 方案：peerDependencies 锁版本范围，或 npm publish 时保持版本一致

## Phase 拆解

1. **Phase 1 ✅** — dist 清理 + shims 内联 + 单配置文件 + 统一类型入口
2. **Phase 2 ✅** — npm pack 验证（15 files, 850KB packed, 3.6MB unpacked，缩了 2/3）
3. **Phase 3 ✅** — 本地安装验证（npm install + CLI + init --dry-run 全正常）
4. **Phase 4 ✅** — npm publish 成功，engine7@7.0.0 上线

## 跨平台验证

- **2026-07-29** 在翀哥 Mac（chongzhang）上完整验证：
  - `npm install -g engine7` → added 160 packages in 59s ✅
  - `engine7 --help` → CLI 正常，中文输出 OK ✅
  - `engine7 init --state-dir ~/test-agent --quick --dry-run` → 路径自动转 /Users/chongzhang/，中文输出正常，目录结构正确 ✅
  - Mac 路径识别、中文打包、跨平台兼容性全部通过

### Phase 1-3 完成
- [x] 调研 dist 目录结构（`ls dist/`）
- [x] 确认 shims/Skills/superpowers/sqlite-vec 现状
- [x] 验证 esbuild/bundle 配置
- [x] 写 docs/todo/ 规划文档（2026-07-29_engine7_npm_publish_plan.md）
- [x] package.json 清理（build script + files 白名单排掉 .map + README.md）
- [x] 写跨平台 build.mjs（替代 rebuild.cmd 的 esbuild 命令）
- [x] 删掉 setup-runtime-modules 引用
- [x] npm pack 验证（sourcemap 排掉，包体缩 2/3）
- [x] 本地安装验证（npm install + CLI + init dry-run）

## 待确认

- shims 引用路径修正方案（package.json 改 bin/main 入口）
- sqlite-vec 跨版本兼容方案（peerDeps vs 锁定版本）
