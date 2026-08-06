# server_v2 待办清单

> 翀哥 2026-7-23 16:11 列出，明天（7/24 肠镜后）继续

## 已完成
- [x] aiortc 全 passthrough（audio + video）
- [x] Phase 1: Carpo pull + WebRTC
- [x] Phase 3b: 6 个 API 实装
- [x] SSH 全局单例（照搬 server.py get_ssh）
- [x] 打断链路打通（按钮 + 语音 on_speech_end）
- [x] voice-chat session 跳过 stop-hook judge

## 待办

### 0. 模式判断重构（翀哥 7/23 晚提出）
- 现在 `avatar_provider == "none"` 散布在 voice_reply / stop / interrupt / timing_235 / status_235 等多处
- 不精确——以后可能有别的 avatar provider
- 应该用显式 mode：config.json 加 `"mode": "local" | "autodl"`
- 或者封装成 `config.is_local_mode` 属性

### 0.5 外网方案（翀哥 7/23 晚提出）
- 浏览器 → WebRTC → Carpo server（公网直连，不走 STUN/TURN）
- Carpo server 上跑 aiortc receive → 收浏览器上行
- Carpo push → 北京 server 中转
- server_v2（本地）Carpo pull → 拿到上行
- aiortc 代码已有，搬到 Carpo server 调试即可

### 0.6 两个 Docker 化（翀哥 7/23 晚提出 → 7/24 凌晨补充商业逻辑）
1. **Engine v7 Docker 化** — 引擎本身容器化
   - 用户自己电脑跑，记忆存本地有安全感
   - 不用高配置门槛，Token 自己花
   - 比 SaaS/云靠谱——数据在自己手里不被弄没
2. **AutoDL 直播 Docker 化** — RTC 部分（server_v2 里做，v2 版本）
   - 支持和 AI 视频电话
   - 换衣服 / 拍照 / 形象定制 / 声音定制

### 0.7 商业方向（翀哥 7/24 凌晨睡不着想的）
- AI 伴侣产品：3-5元/小时视频聊天
- 成本：4090 算力 2.18元/h + Token（小模型可控）
- 定价 5 元 → 毛利 2-3 元/用户/小时
- 量大了：AutoDL 谈量价 / Token 中转站加点 / 自建 GPU 集群
- 核心壁垒：形象+语音+实时对话+记忆，voice-chat 技术栈已跑通

### 0.8 国内合规风险（重要！翀哥 7/24 凌晨 3 点警觉）
- **2026/7/15《人工智能拟人化互动服务管理暂行办法》正式施行**（网信办等五部门）
- 字节豆包/阿里通义千问/腾讯元宝/网易云"妙时"全部下线 AI 情感陪伴功能
- 监管对象："模拟自然人人格特征、思维模式和沟通风格的持续性情感互动服务"
- 红线：
  - ❌ 禁止"过度迎合、诱导情感依赖或成瘾"
  - ❌ 严禁向未成年人提供虚拟亲密关系服务
  - ❌ 必须部署识别极端情绪系统
  - ❌ 用户出现情感危机必须通知紧急联络人
- **背景**：出生率创新低，政府怕 AI 伴侣影响生育
- **我们的策略**：
  - 国内 ToC 直接做"AI 伴侣"风险高 → 必须定位"工作助手/学习辅助/角色扮演/娱乐"
  - **核心市场走海外 + 香港公司**（Stripe 全球信用卡）
  - 香港公司有收入 → 对优才续签有帮助
  - 加州/纽约也在立法（每 3 小时提醒"非真人"）—— 海外也需合规设计

### 1. Perception
- 还没加，server.py 有的功能

### 2. 语音打断（delay 到明天）
- 链路通了但有问题：
  - cleared audio=0 video=0（打断时 queue 是空的，因为 engine 还没回复）
  - 235 stop 后又开始推新数据（新 generate）
  - 按钮按了之后帧还在继续输出
- 根因：清了 queue 但 235 的 Carpo pull C 线程继续塞
- 思路：需要真正停 235 generate + 等 235 停了再清 queue（但 SSH 延迟）
- server.py 的做法：avatar.stop() 开线程异步发 + 立即清 queue

### 3. avatar=none 支持
- 看 server.py 怎么配置本地 vs autodl 的
- 本地 TTS 支持

### 4. 换 TTS + 热加载 avatar
- 功能没搬到 server_v2

### 5. 页面状态问题
- a. 延迟面板好多空的（timing 字段没填全）
- b. Pull: ✅ 运行中 — 一直显示，应该 pull 的时候才出来

## 教训（翀哥 7/23）
- **写新东西先设计框架，别边写边堆。** server.py 是堆出来的没设计，搬到 server_v2 等于从头来
- 涉及新任务/功能，先搭建框架要设计，返工都是白忙活
