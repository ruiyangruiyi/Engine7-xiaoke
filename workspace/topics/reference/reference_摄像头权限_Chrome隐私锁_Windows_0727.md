---
name: Windows Chrome摄像头隐私锁
description: 7/27摄像头占用——Chrome用完摄像头后handle未释放，需chrome://settings/content/camera设允许
type: reference
date: 2026-07-27
---

# Windows Chrome 摄像头隐私锁

7/27 翀哥测试 voice-chat 视频功能时发现：每次刷新页面后摄像头不可用，报 `video unavailable, audio-only mode`。

## 根因

Windows 上 Chrome 使用摄像头后，**camera handle 没有完全释放**。跟代码逻辑无关——即使是正确的 `localStream.getTracks().forEach(t => t.stop())`，Chrome 的摄像头隐私锁（Windows camera privacy setting）仍然会保持占用。

## 症状

- 第一次打开页面：正常获取 video+audio
- 刷新或关闭后重新打开：video 不可用（默认降级 audio-only）
- 需要等一段时间或清权限才能恢复

## 解决方案

浏览器端（非代码层面）：
1. Chrome 地址栏输入 `chrome://settings/content/camera`
2. 把 `localhost:8116` 加入"允许"列表
3. 以后不再需要每次清权限

## 代码层面的缓解

- `startCall` 里 `beforeunload` 事件中调用 `stopCall()` 释放 track（已加）
- 一次性 `getUserMedia({audio, video})` 而不是分两次获取（已改回）
- 但仍无法完全绕过 Windows 隐私锁，需要浏览器权限设置配合
