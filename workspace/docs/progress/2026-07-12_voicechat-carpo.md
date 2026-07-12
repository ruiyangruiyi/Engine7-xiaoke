# Progress 2026-07-12 — VoiceChat + Carpo

> 每日工作状态落盘。nudge 每日 23:00 提醒写一次。

## 活跃项目

| 项目 | 进度 | 卡点 | 下一步 |
|------|------|------|--------|
| v2 carpo bypass 链路 | ✅ 稳定运行 | - | - |
| voice-chat 集成 avatar video | ✅ 稳定运行 | - | - |
| 端到端时延收集 | ✅ timing 面板全亮 | total 偏高 | 首 chunk 0.5s 已达标 |
| **🆕 GPT-SoVITS 逐句请求** | ✅ 首 chunk 14s→1.5s | - | - |
| **🆕 avatar 切换闪现修复** | ✅ 彻底解决 (3行核心代码) | - | - |
| **🆕 settings 状态同步** | ✅ /api/status + /api/status_235 | - | - |
| **🆕 interrupt_mode setting** | ✅ 前端可切换打断模式 | - | - |
| **🆕 CosyVoice 429 兜底** | ✅ raw_q.get timeout 加网兜 | - | - |
| **🆕 GPT-SoVITS 自动拉起** | ✅ start_carpo_avatar.sh 自动启动 + 健康检查 | - | - |
| **🆕 AutoDLAvatar 清理** | ✅ 删 V1 残留 + _busy 状态跟踪 + 死代码清理 | - | - |
| **🆕 Engine hooks 接线** | ✅ PreToolUse/PostToolUse/Stop — commit `cbcfb69a` | 按需降级 | Phase 2 评估 |
| **🆕 SESSION-STATE 重构** | ✅ Phase 结构 + 清 pending → calendar | - | Phase 2 SOP 优化 |
| 打断功能 | 🟡 500ms debounce + 自动打断 | 待测试验证 | 重启验证 |
| Docker 化 | ⬜ 待启动 | 需 carpo_build (已备份) | Dockerfile + Makefile |
| CPU 优化 | 🟡 根因已定位 (Python 数据搬运) | 大重构 | 待翀哥决策 |
| GPT-SoVITS 流式 | ⬜ 逐句已优化 | - | api_v2 streaming_mode |
| 私有 LLM 部署 | ⬜ 低优先级 | 需选型+花钱 | 翀哥决策 |

---

## 🎉 今日通关（7/12）

### 上午：FlashHead 闪现修复（彻底搞定）
1. **server.py 回退到稳定版** (`c0d13d89`) — 先回到 `0af4299a` 基线
2. **GPT-SoVITS 自动拉起** (`9117e547`) — start_carpo_avatar.sh 自动启动 + 9880 端口健康检查
3. **GPT-SoVITS 逐句请求** (`3371310e`) — **首 chunk 14s→1.5s** 🎉
4. **CosyVoice 429 兜底** (`f79ef825`) — raw_q.get timeout 加网兜，防 429 限流崩溃
5. **TTS provider 热切换修复** (`a1f70943`) — rebuild tts instance on hot-swap
6. **interrupt_mode setting** (`6c3a44e7`) — 前端可切换打断模式

### 下午：avatar 切换闪现修复（核心）
7. **switch_avatar 重载 pipeline** (`75d4c8a1`) — 彻底解决闪现旧形象 bug
8. **_inference_lock + _idle_frame 同步** (`ec05d5c7`) — 持锁同步三份缓存
9. **settings 状态同步** (`4c4b7d0c`) — /api/status + /api/status_235 + 前端优先读后端
10. **AutoDLAvatar 清理** (`e076cb6a`) — 删 V1 残留 + _busy 状态跟踪
11. **死代码清理** (`8f281053`) — 删 autodlv2/python/avatar/ 目录
12. **新基线** (`3fb35f23`) — 提交当前稳定版作为新基线

### 晚间：AutoDLAvatar 修复 + hooks + 深度讨论
13. **Carpo pull 生命周期** (`4c514a42` → `c1a6820b` → `d8dd299f`) — WebRTC 建联时启动，Ctrl+C 不卡退出
14. **Engine hooks 接线** (`cbcfb69a`) — PreToolUse/PostToolUse/Stop hooks
15. **nudge 正则修复** (`d6c962c9`) — 匹配标准 markdown task 格式
16. **distill-output.md 加载** (`bf40eb45`) — system prompt 自动加载（小柯+姐姐）
17. **22:30-23:00 跟爹深度讨论** — SOP/SESSION-STATE/hooks/ Phase 结构 → SESSION-STATE 重构

### Commit 统计
- **engine: 29 commits**
- **xiaoke: 0 commits**
- **LovePea: 0 commits**

---

## 🎯 昨日完成 (7/11) — 快速回顾

- GPT-SoVITS TTS 接入 + 运行时切换 provider
- SSH 全局连接池 (get_ssh)
- 延迟面板恢复 + timing key bug 修复
- CPU 根因定位：Python 数据搬运 vs C++ streamer
- libcarpo.so + carpo_build 源码备份到本地 + LovePea/platform/Linux
- 173 机器 onboarding (clone of 235, md5 一致)
- timing 统计修复 (删 timing.update 污染 + copy 快照 + checkpoint)
- autodl_send.py 去硬编码 (读 machines.json)
- 语音打断 500ms debounce 方案 (已改好待测试)
- **24 commits**

---

## 今日计划 (7/12)

### 高优先级
1. **语音打断测试** — 重启 server.py，验证 500ms debounce 效果
   - 正常说话能打断 ✅
   - 咳嗽/叹气不误触发 ✅
   - 打断后 idle 正常 ✅
   - 打断后再说话正常回复 ✅
2. **提交未提交的改动** — server.py 语音打断代码还没 commit