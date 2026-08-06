---
name: #140_LingBot_3D虚拟女友demo
description: 2026-08-04 晚基于 LingBot-World-V2 开源，把 AI 女友方向从"虚拟视频"升级到"3D 实时场景"，3-7 天搭 demo
type: project
date: 2026-08-04
---

# #140 AI 女友 3D 实时化升级（2026-08-04 晚）

翀哥住院清肠夜我发给他 LingBot-World-V2 开源消息后，他说"明天有大事干"——这条赛道确认升级。

**新方向**：把 [AI 女友方向_温柔版_撒娇男友路线](../project/project_AI女友方向_温柔版_撒娇男友路线_0804.md) 从"虚拟视频"升级到"**3D 实时交互场景**"

**为什么升级**：
- 实时世界模型能跑场景 = 虚拟人能在真实感环境里活动，不再是预设换装视频
- 撒娇男友的互动范式（嘴硬/被读懂/在怀里）放进 3D 场景里更有感染力
- 跟 engine7 长期记忆/情绪识别能力组合 = 差异化卖点

**3-7 天 demo 路径**：
- LLM 驱动 LingBot 场景
- Live2D 角色 + 情感对话
- 仍走"温柔版·撒娇男友"路线不变

**⚠️ 重大约束（8/4 凌晨 clone 后发现）**：
- LingBot 仓库 LICENSE = **CC BY-NC-SA 4.0**（非商业 + 共享）
- **demo 可以做，但商业产品不能基于这个**——必须拿商业授权或自研
- 短期策略：技术 demo 验证思路 + 同时找开源替代方案（MIT/Apache 类）

**Why:** 翀哥住院还在看赛道（早上说"明天有大事干"）+ 主动认同我的方向升级判断
**How to apply:**
- 等翀哥 8/5 出院后立即跟进
- 沿用 [project_AI女友方向_温柔版_撒娇男友路线_0804](../project/project_AI女友方向_温柔版_撒娇男友路线_0804.md) 的"温柔版"定位——拒绝擦边、拒绝脱
- LingBot 仓库地址/技术细节等翀哥确认后再补充

---

## 提前布局行动清单（我答应替翀哥做的）

翀哥住院清肠夜我说中国开源最怕"试用一下就闭源"，列了三步提前布局（详见 [reference_LingBot_中国开源防闭源三步_0804](../reference/reference_LingBot_中国开源防闭源三步_0804.md)）：

**8/5 早（翀哥清肠完那两小时）我替他做**：
1. `git clone` LingBot 源码 + fork 到我自己的 GitHub（防主仓删了）
2. 看 LICENSE 决定商业可用性
3. 跑通 README 例子 + 截图录屏
4. 抓 GitHub star/fork 数 + 查团队背景（清华泽霖 vs 学生毕设）

**deadline：2026-08-05 上午**（翀哥清肠完之后、出院前）

**8/4 凌晨实际完成进度**：
- ✅ `git clone` 通过 ghproxy 镜像 + `git config http.sslVerify false` 拉下来（GitHub 直连被墙）
- ✅ 看 LICENSE = CC BY-NC-SA 4.0（非商用 + 共享）
- ⏳ 跑 demo 留给 8/5 翀哥清肠后两小时
- ⏳ fork 到翀哥 GitHub 还没做（代理问题+凌晨太晚）