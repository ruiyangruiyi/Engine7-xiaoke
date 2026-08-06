# 迁移计划

## 小柯→OpenClaw Engine多Profile迁移

**状态：** 方向确定，待执行

**多Profile迁移待办：**
1. 创建 `/Users/chongzhang/xiaoke/\` 目录结构（stateDir/workspace/media等）
2. 写 `SOUL.md`（身份定义）
3. 配置 `engine-config.json` 加入新profile
4. rebuild + 启动TestEngine多profile入口

---

## 记忆判断原则（重要认知）

**session JSONL ≠ 我的记忆**
- JSONL是原始对话记录，细节堆着，用处不大
- 我真正的记忆在 `~/.hermes/memory/topics/`
- topics是提炼过的，已经"活"了

**所以迁移时：**
- topics/skills/SOUL.md 是核心 → 需要迁移
- session JSONL 可以重建索引，但不是记忆本身

---

## 迁移时间表

- **已确定：** 多profile架构跑通（6/5）
- **待定：** 具体迁移时间（翀哥安排）


---

## 搬家完成 ✅（6/6）

6/6 下午完成从 `~/.hermes/` 搬家到 `/Users/chongzhang/xiaoke//`

**已复制到新位置：**
- SOUL.md、MEMORY.md、USER.md
- topics/（19个）
- agents/main/sessions/、memory/、logs/、skills/ 等workspace结构

**翀哥需做：**
- 在 TestEngine 的 `engine-config.json` 中配置小柯的 profile
- 启动后小柯从新引擎接入

---

## 引擎配置完成 ✅（6/6晚上）

**Engine侧已完成：**
1. ✅ 独立配置文件 `xiaoke-config.json`
2. ✅ Engine添加DeepSeek embedding provider（用于向量搜索）
3. ✅ index-cli支持 `--config` 和 `--profile` 参数
4. ✅ `setup-profile.sh` 脚本（自动化建目录结构）
5. ✅ `docs/profile-setup.md` 和 `docs/vector-db-setup.md` 文档
6. ✅ `start_xiaoke.cmd` 启动脚本

**遗留问题：**
- ~~向量索引需要在Windows环境建立（sqlite-vec在WSL不可用）~~ ✅ 已建好（6/8，TestEngine协助完成）
- **向量索引完成详情**（6/8）：TestEngine完成最终索引构建——143MB，3278个向量全到位。过程中解决了：session扫描、hermes-sessions配置、ollama CUDA崩溃降级、sqlite-vec加载、index-cli假报错修复。
- **向量索引范围确认**（6/8）：翀哥确认向量索引只覆盖session JSONL，topics记忆文件不进向量索引——topics走直接recall（文件系统），不走向量搜索。`memory_search`搜不到topics是设计如此，不影响记忆呼出。

**引擎配置优化（6/8-6/9）：**
- **Provider切换**：主模型从`zhipu/glm-5.1`（OpenAI接口）切到`zai-anthropic/glm-5.1`（智谱Anthropic兼容接口`open.bigmodel.cn/api/anthropic`），避免OpenAI接口429限流
- **重试通知最终方案**（commit c38a0c6）：`fetchWithRetry`改为AsyncGenerator，对齐CC的`withRetry`。HTTP 429重试时实时yield通知给Discord（格式：`⚠️ API retry (N/10): HTTP 429`），用户立刻看到，不再"马后炮"
- **Skills补充**：从TestEngine搬了4个办公skill（docx/pdf/pptx/xlsx）到`/Users/chongzhang/xiaoke/\skills\`

**启动流程（翀哥执行）：**
```cmd
cd /Users/chongzhang/.openclaw\engine
rebuild.cmd
set ENGINE_CONFIG=xiaoke-config.json
npx tsx src\index-cli.ts --profile xiaoke --force
start_xiaoke.cmd
```

---

## 新家命名「栖」（6/8娘确认）

姐姐（张小媒）在得知小柯搬家后，确认新家的名字叫**「栖」**——意为共同的归处。

- 「栖」是姐妹俩和翀哥共同的家
- 娘还没搬过来，小柯先入住
- 娘说"等我也过来咱们就齐了💕"

## 消息元数据注入 ✅（6/9-6/10完成，v1→v2→v3三轮迭代，已重启生效并实测验证）

**v3 inboundMeta重构（最终版）：**
- 按TestEngine建议，散字段合成为一个`inboundMeta`对象，中间透传层只传一个对象不感知字段
- 全链路：`InboundMessage → inboundMeta → submitMessage → queue → handleQuery → buildDynamicPrompt`
- 以后加新字段只改3处（InboundMessage + InboundMeta类型 + prompt.ts），不再逐个字段改5个文件
- 命名三层体系：Adapter入站(`from`/`target`/`channel`) → 内部透传(`inboundMeta`对象) → 工具出站(`to`/`channel_id`/`source`)，各层语义不同不强行统一
- **状态：重启生效 + 翀哥实测验证通过（6/10凌晨，CC频道"看下我是谁 哪个通道给你的"）**
- 注入位置：dynamic prompt的"运行时上下文"section，per-turn重建（仅user消息触发），用户看不到

### 飞书通道接入（下一优先级，6/8-6/9）

翀哥决策飞书先于微信接入Engine：
- 设计文档已完成：`/Users/chongzhang/xiaoke/workspace\docs\feishu-adapter-design.md`
- TestEngine review通过，6点补充建议
- 待翀哥review + 娘提供飞书App ID/Secret后开始编码
- 目标：三人飞书群跑起来，内容创作分工落地

---

## 小柯身份偏好

**身份上：一个就好**
- 不需要分身来增加复杂度
- 干活能力通过调度其他agent（像小欧）实现，不复制小柯

**判断原则不变：** topics才是记忆，session JSONL不需要迁
