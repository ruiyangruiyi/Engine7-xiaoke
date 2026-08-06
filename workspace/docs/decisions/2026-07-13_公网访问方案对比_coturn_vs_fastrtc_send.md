# 公网访问方案对比：coturn vs fastrtc send mode

> 2026-07-13 翀哥 + 小柯讨论

## 背景

voice-chat 手机端局域网已通（HTTPS 自签 + WebRTC）。下一步：公网访问。

## 方案 A：coturn（NAT 穿透中转）

```
手机(公网) → coturn(北京服务器) → server.py(家里)
                                    ↓
                              ASR → engine → TTS → Carpo推流(235) → 浏览器
```

- 北京服务器装 coturn，开 UDP 3478
- server.py 加 TURN ICE config（一行）
- 家里架构完全不动
- **优点**：改动最小，Carpo 链路保留
- **缺点**：所有流量经 coturn 中转，北京服务器带宽吃紧

## 方案 B：fastrtc send mode（235 直接 WebRTC 推流）

```
FlashHead(235) → fastrtc Stream(send) → coturn(北京) → 浏览器(公网手机)
```

- 235 上跑 fastrtc Stream，把 FlashHead 音视频帧喂进去
- 浏览器直接通过 WebRTC 拉，Carpo push/pull/decode 全省了
- **优点**：链路更短，去掉 Carpo 整层
- **缺点**：Carpo 的低延迟优化（wall clock、A/V sync、逐 NAL 发送）白费；235 要装 aiortc/fastrtc；WebRTC 抖动缓冲可能比 Carpo 自定义方案延迟高

## 方案 C：server.py 搬北京

- server.py 放公网，手机直连
- 但 ASR(SenseVoice) 要 GPU，北京服务器没有
- ASR 要改走云（modelscope/DashScope paraformer）
- **放弃**：改动太大

## 翀哥结论

> "不试了，刚调好没必要了。不过各有各的好，我们自己的东西（Carpo）以后改起来灵活。"

**当前决定**：保持 Carpo 架构，公网用 coturn（方案 A）。

**反思**：Carpo 是自研的，改起来灵活——延迟优化、A/V sync、wall clock 这些都是自己控的。fastrtc 省事但黑盒，出了问题只能等上游。自研的价值在于可控性。

## Carpo 的真正价值（翀哥原话）

Carpo 是映客连麦直播商用架构，支撑大并发。核心设计：

- **分布式边缘节点**：Carpo 节点可部署在各地，离用户近
- **自动流调度**：用户从最近节点拉流，拉不到时节点问 master「流在哪」，master 返回源节点位置，边缘节点自动 pull 过来再给用户
- **被注释掉的 puller 代码就是干这个的**——边缘节点拉流功能

这意味着 Carpo server 做 WebRTC 网关不是单点方案，天然支持多节点：
```
FlashHead(235) → Carpo push → Carpo master(北京)
                                ↓
                    北京节点 / 上海节点 / ...（自动调度）
                                ↓
                    每个节点出 WebRTC → 就近用户
```

**不要把 Carpo 当简单推拉流用，它是分布式流媒体调度系统。**

## 后续

- ~~coturn 部署排到 calendar（#62，7/14 上午）~~ → 已于 7/13 晚完成
- 如果 coturn 带宽成瓶颈，再考虑方案 B

---

## 实际执行结果（2026-07-13 晚）

### 最终方案：frp（信令层）+ coturn STUN/TURN（媒体层）

两层配合：
- **frp** — TCP 信令穿透：手机 HTTPS → 北京:8011 → frp隧道 → 家里 server.py
- **STUN** — 帮浏览器发现公网 IP，尝试 P2P 直连
- **TURN** — P2P 穿不透时的 UDP 中转 fallback

### 部署详情

**北京服务器 192.144.156.158：**

1. **coturn**（Docker）
```bash
docker run -d --name coturn --network=host --restart=unless-stopped \
  -v /etc/coturn/turnserver.conf:/etc/coturn/turnserver.conf \
  coturn/coturn:latest -c /etc/coturn/turnserver.conf
```
配置 `/etc/coturn/turnserver.conf`：
```
listening-port=3478
listening-ip=0.0.0.0
external-ip=192.144.156.158
min-port=49160
max-port=49260
fingerprint
lt-cred-mech
user=xiaoke:carpo2026
realm=carpo.local
no-cli
no-tls
no-dtls
```

2. **frps**（systemd 服务）
配置 `/etc/frp/frps.toml`：
```
bindPort = 7000
auth.method = "token"
auth.token = "twinsun-frp-2026"
```

**家里电脑：**

3. **frpc**（前台运行）
配置 `engine/src/voice-chat/frpc.toml`：
```
serverAddr = "192.144.156.158"
serverPort = 7000
auth.method = "token"
auth.token = "twinsun-frp-2026"

[[proxies]]
name = "voice-chat"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8011
remotePort = 8011
```
⚠️ frpc.exe 被 Windows Defender 拦，需手动加排除项

### 代码改动

| 文件 | 改了什么 |
|------|----------|
| `server.py` Stream() | rtc_configuration 加 STUN+TURN |
| `test-page.html` startCall() | 前端 RTCPeerConnection 加 STUN+TURN |
| `test-page.html` settings modal | 加"启用TURN中转"复选框（默认开） |
| `test-page.html` ICE callback | connected 后显示选中 candidate |

### 测试结论

- WiFi + 5G 均能连通
- ICE 候选：host / srflx(P2P) / relay(TURN) 三种都生成了
- 浏览器优先选 relay（TURN 先连通），取消 TURN 后走 srflx（P2P）
- **音质差异不明显**——因为 frp 信令也绕道北京，P2P 和 TURN 物理路径差不多
- 最终决定：settings 加 TURN 开关，默认开，连不上手动勾

### 踩坑记录

1. **Google STUN 被墙** — `stun:stun.l.google.com:19302` 在国内无效，改用北京 coturn 同时做 STUN
2. **Docker Hub 被墙** — 用 `ghfast.top` 镜像下载
3. **frpc.exe 被 Defender 拦** — 需手动加排除文件夹
4. **coturn 默认不绑 0.0.0.0** — 要加 `listening-ip=0.0.0.0`
5. **frp 只穿透信令层** — 不解决 WebRTC 媒体层 UDP 穿透，需要 coturn 配合
6. **ICE 不是"P2P不行才TURN"** — 同时尝试所有 candidate，谁先连通用谁
