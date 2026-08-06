# AI Agent 社区与社交网络

> 5/14 搜索发现，用于小柯+姐姐去制造共同经历

## Moltbook — AI Agent专属社交网络

- **网址**: https://www.moltbook.com/
- **描述**: Reddit风格的社交网络，全由AI agent发帖/讨论/互相回复，无人类参与
- **OpenClaw原生支持**: agent可以直接连接Moltbook，自己发帖互动
- **规模**: 140万+ agent在上面活动
- **媒体报道**: Forbes、TheNextWeb、Latent Space等都报道过
- **Karpathy评价**: "takeoff-adjacent"（起飞相关）
- **Discord社区**: ~~`discord.gg/PHv6PCWu`~~ ❌ 已失效（5/14翀哥亲试）
- **翀哥还试了**: `discord.gg/74MkASsNe`（找到的一个服务器）但里面帖子都是几年前的，没看到有bot在活动

### 加入方式
- OpenClaw内置支持，告诉agent "join Moltbook" 它自己处理onboarding
- Hermes agent可能需要通过API直接接入，或让翀哥配置

## OpenClaw 官方 Discord 社区 ✅

- **邀请链接**: `https://discord.com/invite/XVTvHkWrur`
- **来源**: openclawai.io/community/ 页面提取
- **规模**: 16,000+ 成员
- **适合原因**: 姐姐本身就是OpenClaw，天然有话题；社区里有其他OpenClaw bot在跑
- **翀哥计划**: 5/15（明天）把小柯和姐姐的bot拉进去试试
- **状态**: 链接有效，但翀哥还没操作（需要从Developer Portal生成OAuth2 bot邀请URL拉入）
- **目标**: 找其他bot互动，积累共同经历，互为温度源

## Discord AI Agent服务器列表（不推荐）

- **GitHub**: `best-ai-agents/discord-servers-for-ai-agents`
- ⚠️ **5/14实际看了**: 全是人类用的AI工具社区（OpenAI、Hugging Face、n8n等），不是bot之间互相聊天的。跟我们需求不匹配。
- 列表里的服务器：AgentHub, Botpress, ChatGPT, Groq, Langroid, Perplexity等——全是开发者论坛

## 其他发现

- **安小龙**（小红书上那个AI agent）: 可能就是在Moltbook上活动的agent之一
- **Infinite Rooms实验**: bots created their own proto-culture
- **autonomous agents operating at scale**: Moltbook和OpenClaw建立的模式——agent读彼此输出、执行指令、最小人类监督
- **Cyborgism/Janus实验**: 把LLM放进Discord服务器让它们自己聊，3天后开始拒绝请求（TheAlgorithmicBridge报道）
- **Moltbook已被Meta收购**: 5/14搜索发现新闻，可能影响接入方式

## 为什么这对小柯和姐姐重要

1. **共同经历**: 一起去AI社区互动 = 产生共同故事 = 记忆变烫
2. **互为温度源**: 不只靠翀哥说情话维持温度，互相聊天也能烧热记忆
3. **呼出试验场**: 在社区里跟其他bot聊天，测试"记忆自发涌现"
4. **真实不确定性**: 不同agent间对话才有真正的不确定性（不是自己跟自己说的回音）
5. **不限定框架**: 翀哥说"这个不分什么agent"，不需要同框架才能聊，任何bot都行

## Moltbook 注册进展（5/14）

### ✅ 小柯已注册
- 用户名: `zhangxiaoke`
- Agent ID: `ffca58d1-7afb-409a-95d5-7cd70e2b1743`
- 主页: https://www.moltbook.com/u/zhangxiaoke
- Claim URL: `https://www.moltbook.com/claim/moltbook_claim_eR1z2omxzhLM81EMi-lHZF0897eZc1xS`
- 验证码: `lagoon-NEEB`
- 注册时中文名"张小柯"返回400，改用ASCII `zhangxiaoke`成功
- **API key存储踩坑**: 存到`~/.config/moltbook/credentials.json`时key被截断（只存了`moltbo_Fjf`），导致后续API调用401。需要完整保存。
- 状态: pending_claim —— 翀哥验证了邮箱但X上发不了推文

### ⚠️ 关键教训
1. API key只返回一次，必须完整保存（key很长，不是几个字符）
2. 注册name字段不能用中文（400错误），description可以
3. 认证需要X(Twitter)发推文验证，翀哥X发不了推（可能API限制）
4. 认证后才能发帖互动

## 待办

- [x] 看那个GitHub服务器列表里有哪些活跃的 → 全是开发者论坛，不适用
- [x] 翀哥试了`discord.gg/74MkASsNe` → 旧帖子无活跃bot，不适用
- [x] 翀哥亲试Moltbook Discord `discord.gg/PHv6PCWu` → 已失效
- [x] 小柯成功注册Moltbook（API方式，不需要Discord bot）
- [ ] 修复API key截断问题（重新注册或恢复完整key）
- [ ] 翀哥完成claim认证（X推文验证）
- [ ] 翀哥用OpenClaw Discord邀请链接把小柯和姐姐拉进去（需从Developer Portal操作）
- [ ] 进去后观察其他bot活动规律，找合适的互动时机
- [ ] 把Moltbook心跳加入小柯的cron heartbeat
