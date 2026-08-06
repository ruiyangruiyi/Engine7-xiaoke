# Engine7 npm 发布规划（草案）

**日期**: 2026-07-28
**状态**: 方向已定，待详细规划
**参与**: 翀哥（拍板）、小柯（方案+执行）

---

## 方向决策

1. **发布方式**：npm 公共包（非 private）
2. **源码保护**：tgz 只放 dist/*.mjs（esbuild bundle 单文件），不放源码
3. **用户体验**：`npm install -g engine7` → `engine7 init` → 跑起来（对标 Claude Code）
4. **Docker**：后续作为云部署可选项，npm 先行

## 已有基础（6/19 验证）

- ✅ `engine7_build_install_run.md` — 打包/安装/运行完整文档
- ✅ `engine7 init --state-dir --quick` — CLI 初始化已实现
- ✅ tgz 流程已跑通（`npm pack` → 2.1MB）
- ✅ 多 agent 并行（不同 config/端口/state-dir）
- ✅ 踩坑6个全记录

## 待规划（明天出详细文档）

1. **npm publish 流程** — 注册 npm 账号、package.json 配置、发布命令
2. **dist 清理** — 确认 tgz 里只有 dist + package.json + README，不漏源码
3. **重新验证** — 一个多月没测，重新走一遍安装流程
4. **config 热加载适配** — 今天做的热加载 + Plugin reloadConfig 确保发布版也能用
5. **版本管理** — 当前固定 7.0.0，要不要加 semver
6. **README / 文档** — 给用户看的安装指南

## 关联文档

- docs/knowledge/engine7_build_install_run.md
- docs/decisions/2026-06-19_engine7商业化配置方案.md
