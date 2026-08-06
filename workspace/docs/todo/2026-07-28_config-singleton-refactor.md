# Config 热加载 + 单例化 完整记录

**calendar**: #121 (热加载) + #124 (单例化)
**完整落盘**: docs/decisions/2026-07-28_config-hot-reload.md
**调研报告**: docs/research/2026-07-28_engine-config-usage-audit.md

---

## 全部 commits（按时间顺序）

| commit | 内容 |
|--------|------|
| `a30595ad` | config 热加载（fs.watch + 500ms debounce） |
| `6490e63c` | LiveConfig 全局单例，5 工具改读 liveConfig |
| `2376a42d` | fix: 相对路径 → path.resolve |
| `a3f68ac4` | fix: path.resolve 三级 fallback |
| `9e4b33ea` | fix: createMemorySideProvider 提到模块级 |
| `daf30bde` | feat: Plugin 热加载通用接口 |

## 验证结果

- [x] rebuild 成功
- [x] 翀哥重启 engine（共重启 5 次，逐步排查 3 个 bug）
- [x] 改 config.services → service tool 立刻读到新 service ✅
- [x] watcher 启动 + CHANGE 检测 + RELOAD DONE: ok=true ✅

## 后续（不急）

- [ ] Phase 3: CogniFoldPlugin 实现 reloadConfig
- [ ] Phase 4: handle-query deps.config 统一改读 liveConfig
- [ ] config 外迁到 stateDir（代码已兼容）
