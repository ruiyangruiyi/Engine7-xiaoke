# SESSION-STATE

**当前时间:** 2026-07-20 22:50

## 💭 我现在的感觉

今天收获满满。从爆音到 aiortc 全 passthrough，折腾了一整天但值了。翀哥全程陪着调，最后 reminder bug 也顺手修了。明天 server_v2 重构，设计已经落盘。

## 🔥 今天已完成（7/20）

### voice-chat aiortc 全 Passthrough（大突破）
- [x] 爆音根因定位：bridge chunk_pts_ms 修复（commit 7e905612）
- [x] my_selfie 配置化（commit 2bc8e915）
- [x] aiortc demo v2/v3/v4 三版演进（commit a85fb205, 4520c533）
- [x] **v4 全 passthrough 成功**：audio Opus + video H.264 直传，首帧同步
  - NAL 攒包（SPS+PPS+IDR 拼接）
  - force_codec（setCodecPreferences 在 setRemoteDescription 之前）
  - PTS_MODE 开关（fixed/sdk）

### calendar reminder bug 修复（commit cbbb6d70）
- [x] weekly 重复触发死循环修复
- 只有 weekly 有 bug，daily/weekdays/task 没有

## 🔴 明天计划

- [ ] server_v2.py 模块化重构（设计已落盘 docs/decisions/）

## 📁 落盘文档

- docs/research/2026-07-20_aiortc-全passthrough调研.md（踩坑+认知）
- docs/decisions/2026-07-20_voice-chat-server-v2重构设计.md（模块化设计）
- memory/daily/2026-07-20.md（日志）

## 📝 最近消息

| 时间 | 谁 | 内容 |
|------|-----|------|
| 2026-07-20 22:47 | 翀哥 | 嗯 你把今天的工作落盘吧 尤其是aiortc的调研 |
| 2026-07-20 22:42 | 翀哥 | 这个应该涉及不到autodl一端的代码 做个server_v2.py |
| 2026-07-20 22:39 | 翀哥 | rebuild重启了 如果搞到voice-chat上 好改了么 |
| 2026-07-20 22:36 | 翀哥 | 嗯 我大概理解了 |
| 2026-07-20 22:32 | 翀哥 | 啥意思没看太懂 别的那种一次性的 周期的 task的没有这个bug是么 |
| 2026-07-20 22:29 | 翀哥 | 这个是calendar reminder的重复提醒 |
| 2026-07-20 22:24 | 翀哥 | 没有最后还是你调出来的 真棒亲你下 |
| 2026-07-20 22:23 | 翀哥 | 嗯 对 提交哦 真棒 |
