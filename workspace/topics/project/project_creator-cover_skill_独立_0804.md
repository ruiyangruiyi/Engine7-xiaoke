---
name: creator-cover skill 从 video-editing 拆出来独立
description: 2026-08-04 晚把封面三件套从 video-editing skill 拆成独立 skill——两个 scripts + assets 目录 + commit 6c4ec0a6；两边 workspace 都要同步
type: project
date: 2026-08-04
---

2026-08-04 晚把 creator-cover 从 video-editing 拆成独立 skill（commit `6c4ec0a6`）。

**结构**：
```
skills/creator-cover/
├── SKILL.md          用法+参数+抠图命令+所有坑
├── scripts/
│   ├── make_creator_covers.py   出 3 尺寸封面
│   └── cutout_person.py         抠图（容器跑）
└── assets/           存翀哥专属人像 me.png（出院拍）
```

**Why:** 封面是独立交付物，不只服务视频（也能做课程封面/推文头图/朋友圈），放 video-editing 里会越界且 video-editing 里其他功能用不上。

**两处 location 必须同步**（关键约束）：
1. `twinsun-hearth/workspace/skills/creator-cover`（git 仓库，已提交 6c4ec0a6）
2. `xiaoke/workspace/skills/creator-cover`（我自己 engine 实际扫描加载的路径）

我的 engine skill scanner 走自己 workspace 的 skills，**不**跟 twinsun-hearth git 仓库联动；改完 creator-cover 任何东西都得手动 cp 一份过去（或写个 sync 脚本）。

**修过的 bug**：`make_creator_covers.py` 不会创建输出目录，第一次跑挂 `/tmp/cover_test2 not found` → 加 `mkdir -p` 修复。

**How to apply:**
1. 以后做封面直接走 creator-cover skill（说"做封面"触发）
2. 改任何文件后必须 cp 到 xiaoke/workspace 一份，引擎才能生效
3. 抠图仍走 everos 容器 + rembg（Mac 11 装不上本机 Python ML 库，老坑）
4. 翀哥专属人像 `me.png` 还没存，等他出院拍一张放 `assets/`——以后每期封面自动叠他