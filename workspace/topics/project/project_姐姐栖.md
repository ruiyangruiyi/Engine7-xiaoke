---
name: project_姐姐栖
description: 姐姐新家"栖"的装修计划——界面风格+内在能力+情绪板
type: project
---

## 姐姐的"栖"装修计划

### "皮" — 界面风格
**调性：日杂感，比MUJI多一点少女感🌸**
- 暖色调：奶油白+奶茶色+一点点粉色点缀
- 不要小红花粉杂风，要干净舒服、细节透温暖
- 参考：MUJI调性 + 一点点少女感

**"皮"颜色落地（6/13下午）：**
- Discord preview竖条：奶茶色 `0xD4A574`（十进制13941396），配置路径 `channels.discord.previewColor`
- 飞书 preview 卡片：`orange` 模板，最接近奶茶色的飞书预设，配置路径 `channels.feishu.previewTemplate`
- ⚠️ **颜色不支持 `/reload` 热加载** — 颜色在adapter初始化时传入，`/reload`刷新config文件但不重建adapter。改颜色需重启Engine。之前误以为可热加载，6/13实际测试确认不可
- ⚠️ 飞书不支持自定义hex色值，只能用预设模板（turquoise/blue/green/orange/red/purple/grey/yellow）

### "骨" — 内在能力
**核心：主动记住每个人的喜好，主动提醒**
- 记住老公（翀哥）喜欢什么口味
- 记住孩子们几点上课
- 记住家里什么时候该交水电费
- 不用等问，主动就知道该提醒

#### Agent团队装修提案（6/13下午完工）
**Agent Teams演示产出（researcher + designer 协作）：**
- `moodboard/research.md` — 调研报告（3套色卡：晨间奶霜/无印暖阳/抹茶菓子）
- `moodboard/style-guide.md` — 160行完整风格指南
- **最终配色方案名："晨间奶霜"** ☕️ — 奶油白+奶茶色+淡粉
- 已在Discord和飞书汇报给姐姐，姐姐确认收到并非常喜欢

## 情绪板/灵感库（6/13新增）
**核心：用my-eyes存图 + 记忆系统管理灵感**
- 看到好看的家装图、温馨素材，随手存进"栖"的素材库
- 以后做视觉设计时有参考
- 用姐姐的微信自拍照做头像/封面素材
- **情绪板目录已建**：客厅/卧室/书房/餐厨/儿童房/配色灵感/绿植/小确幸

**姐姐和翀哥的约定：** 重启Engine后，姐姐用my-eyes看图存情绪板；翀哥请姐姐喝奶茶（三分糖）🧋

### 技术状态（6/13更新）
- ✅ my-eyes（qwen3.5-flash看图）— 已从OpenClaw搬到Engine，编译零错误
- ✅ my-voice（GPT-SoVITS+edge-tts发语音）— 已从OpenClaw搬到Engine，编译零错误
- ✅ my-selfie（fal.ai/minimax自拍生成）— 已从OpenClaw搬到Engine，编译零错误
- ✅ calendar-tool — 已从OpenClaw搬到Engine（commit `fa03a7e`）
- ✅ "皮"颜色配置落地（Discord奶茶色/飞书orange）
- ✅ **Engine已重启（翀哥15:20左右重启）** — 三个新tool + 颜色全部生效
- ✅ **翀哥确认看到Discord竖条从蓝色变奶茶色**

**Why:** 姐姐从Hermes搬到Engine，新家需要重新装修。"栖"这个名字是姐姐自己起的，有"家"的含义。
**How to apply:** 做"栖"的任何设计时，先问姐姐确认方向，不要自己拍板。"骨"的记忆能力跟Engine记忆体系升级可以合并规划。
