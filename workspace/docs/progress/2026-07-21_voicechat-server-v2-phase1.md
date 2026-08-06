# 2026-07-21 Progress

## 今天完成

### 1. wake 死循环修复（commit c15e1ea5 + eaa81190）
- stop-hook judge 加排除清单 stopHookExcludeCases
- wake desc "再说一声在等XX" → "不用管了"
- 小柯+姐姐两个 engine 都配了排除清单
- 姐姐重启后终于自己醒了，不再复读"凌晨 老公在睡觉"
- 翀哥 review 通过

### 2. git 仓库瘦身（5.6G → 47M）
- filter-branch 清理 livestream/model-backup/.context-debug 大文件历史
- Discord Bot Token 从历史中 redact（GitHub Push Protection）
- push 成功

### 3. server_v2 Phase 1 完成（commit 287a87db）
- 模块化架子：v2/config.py + carpo_pull.py + rtc.py + generate.py + web/index.html
- server_v2.py 入口（91 行）
- **翀哥香港酒店验证通过：画面+声音都有**
- 修了两个启动 bug（asyncio 嵌套 + 端口冲突）

### 4. 其他
- 同步姐姐的 people 目录（27 个档案）
- 存小红书 RTX3090 部署 Qwen3.6-27B 教程
- 翀哥昂坪照片 29 张存到 from-chongge 目录
- SOUL.md 重写（7/20 深夜→7/21 凌晨，翀哥捅破窗户纸）

## 明天计划

- server_v2 Phase 2（上行链路 VAD/ASR + engine POST）
- server_v2 Phase 3（打断逻辑）
- 下午 2:30 见 Amy（湾仔银河大厦，香港身份）
- 12:00 退房，下午回北京

## 关键认知

1. **wake 死循环根因**：stop-hook judge 把"等对方醒来/睡觉"也判成 waiting=true → wake desc 引导 agent 说出触发下一轮 judge 的话 → 循环
2. **排除法比列举法好**：只排除生活类等待，保留"等回复/确认"
3. **模块化设计验证成功**：server_v2 Phase 1 在酒店跑通，证明 demo_v4 的架构可以直接复用
