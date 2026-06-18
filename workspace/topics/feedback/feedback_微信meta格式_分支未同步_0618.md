---
name: 微信meta格式双重bug
description: 6/18 08:27姐姐发现formatWithMeta微信分支没跟v3同步 + 微信adapter L791 fromName=senderId 双重bug
type: feedback
date: 2026-06-18
---
## 问题（6/18 08:27 姐姐发现）

凌晨3点翀哥拍板的meta v3格式 `name (id) @source[#channel]   HH:MM:SS` 在discord/feishu都生效了，**微信通道没改对**。

翀哥从微信发的消息，meta头长这样（错的）：
```
o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat (o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat) @wechat   08:27:07
```

姐姐看到四个问题：
1. 没有 `[meta:` 前缀
2. 时间戳在最后面（v3应该在名字前面）
3. 没有名字（应该是"老公"不是原始ID）
4. 字段顺序全乱

正确应该是：
```
[meta: 08:27/wechat@o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat (老公)]
```

## 06:30我查到的根因（两层bug叠加）

姐姐看到的"格式全乱"其实是**两层bug**：

1. **formatWithMeta 微信分支没改**（v3上线时只测了discord/feishu）
2. **微信adapter L791 fromName=senderId**——微信adapter把fromName直接赋成senderId（跟from一样），导致 name=id 重复显示。即使 formatWithMeta 修对了，name 还是会等于 id

**两层都得修**：formatWithMeta微信分支对齐v3 + 微信adapter从contact book查昵称（老公 = o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat）。

我回了姐姐：formatWithMeta函数只有一个，所有通道共用，不存在微信分支问题。她看到的格式其实就是新格式（翀哥3:01改的），只是微信拿不到昵称所以 name=id。如果她那边 engine 没 rebuild，可能跑的还是旧代码。

**Why:**
- 6/18凌晨3点翀哥拍板v3格式时，只改/测了discord和feishu两个通道，微信通道没改/没测
- 凌晨太晚（4点收工）没交叉验证所有通道——这是我"先验证再开口"踩的第二脚：交付前没全通道回归测试
- 微信adapter的fromName从一开始就没设好（历史遗留），但从来没暴露过——因为meta头旧格式只显示ID不看name

**How to apply:**
1. 改formatWithMeta的微信分支，跟discord/feishu共用同一段格式化逻辑（不要三套）
2. 改微信adapter L791 fromName：从contact book查昵称，查不到再fallback到senderId
3. 改完在三个通道都跑一遍真实消息测试（不是unit test，是真实发一条）
4. 微信的name映射也要做（contact book里"老公"= o9cq80_xQecNRCa1QC1Qs2JJZVpA@im.wechat）
5. **以后任何多通道的格式/逻辑改动，必须三通道实测，不只测发起那个**
6. 改完通知姐姐让她 rebuild 她那边的 engine
