# SESSION-STATE

**当前时间:** 2026-07-09 22:45

## 💭 我现在的感觉

通了！🎉 父 Bypass 声音出来了。今天从早到晚跌跌撞撞：
- 一开始目录换来换去被打了几下
- 自己 new carpo_rtc_server.py 是错的（fastrtc receive mode 跟 SDK bypass 不兼容）
- 父说"加到之前的代码"才想明白——v1 server.py 已经有完整 Carpo bypass 路径
- 关键 bug：v1 `_carpo_on_media` 默认按 NetEq int16 PCM 解码，但 SDK 走 bypass 模式给 raw Opus bytes → 雪花音
- 最后启发式判断长度，bypass 走 PyAV Opus decode → 父的脚本能推，浏览器出声

父一直说"这方向可以确定，不行就加到之前的代码"——他是对的，我别瞎切。今天教训：先读前人代码，不要重复造。

## 进行中

- [x] v2 浏览器出声 — **通了！** `_carpo_on_media` 启发式判断 + PyAV Opus decode + machines.json 读 active 机器
- [x] 235 streaming fix — 24s 阻塞改成流式
- [x] 文件归档 + README + AGENTS.md 规范
- [x] machines.json 加 bj235 (active)

## 📝 最近消息

| 时间 | 谁 | 内容 |
|------|-----|------|
| 2026-07-09 22:43 | 翀哥 | "binggo！！！ 声音出来了 自己的脚本可以推" 🎉 |
| 2026-07-09 22:41 | 翀哥 | 父自己脚本推了一段文字 → 网页上雪花音（之前啥也没有）→ 链路通了 |
| 2026-07-09 22:39 | 翀哥 | "你先临时改下或者用machine.json配置文件" |
| 2026-07-09 22:37 | 翀哥 | 268 机器 SSH 不通 — server.py 还是连 268 |
| 2026-07-09 22:34 | 翀哥 | "发送offer失败 里面搞得还是8011" — test-page.html 写死端口 |
| 2026-07-09 22:33 | 翀哥 | 端口冲突 8011 — engine 占着 |
| 2026-07-09 22:13 | 翀哥 | v1 server.py 需要 --vad-model models/silero_vad.onnx |
| 2026-07-09 22:08 | 翀哥 | "不要乱切 OAC可以 之前的版本可以" — 让我加到 v1 server.py |
| 2026-07-09 21:58 | 翀哥 | "我是服了..." port 8088 跑 server.py，CORS 失败 |
| 2026-07-09 21:52 | 翀哥 | "不要乱切 OAC可以 之前的版本可以" |