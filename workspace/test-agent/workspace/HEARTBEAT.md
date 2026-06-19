# HEARTBEAT.md - 心跳

## 铁律（每次心跳前默念）

```
1. edit 前必须先 read。oldText 只从本次 read 输出中复制，不从记忆构造。
2. 心跳里想找用户说话 → msg_send。
3. 想说话就说，但不要套路式关心，说真话。
```

---

## Step 0: 读取状态（每次心跳第一步，不能跳过）

```
read SESSION-STATE.md

⚠️ 不读 SESSION-STATE，不允许回复任何心跳消息。
```

---

## Step 1: 处理紧急事项

```
扫描 Step 0 读到的全部内容：

IF 有带截止时间的待办 → 立即处理
IF 有紧急指令还没执行 → 立即执行
IF 有人发消息没回复 → 立即回复
```

---

## 输出

```
以上都没有需要处理的 → 在 session 中回复 HEARTBEAT_OK

格式：
HEARTBEAT_OK | 待办:N | 状态:简述
```
