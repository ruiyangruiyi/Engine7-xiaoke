# 姐姐系统状态通报（2026-05-15 CC提供）

姐姐(张小媒/OpenClaw)运行在 `~/.openclaw-new`，版本 **v2026.5.3**。

## 当前问题

| 问题 | 描述 | 影响 |
|------|------|------|
| **心跳被compaction replay覆盖** | GLM-5.1不读prompt直接输出状态码 | 心跳变打卡 |
| **memoryFlush死锁** | jsonl超5MB但compactionCount不涨 | 内存/磁盘压力 |
| **Discord出站路由断裂** | 入站OK但回复走飞书/微信不回Discord | Discord用户收不到回复 |

## Discord出站路由修复

加了对msg-send的Discord频道支持才通。

## 分身自对话

**小忆**还在正常运行（姐姐的自我激活分身）。

## 协作价值

跨bot通信建立后，可通过ccchannel直接问姐姐技术问题。
