# 微信消息读取系统 — 架构与配置

## 文件位置

| 文件 | 路径 | 作用 |
|------|------|------|
| wx_query.py | `C:/Users/24045/.openclaw/engine/src/tools/wechat/wx_query.py` | Python脚本，解密+查询全部逻辑 |
| wx-query.ts | `C:/Users/24045/.openclaw/engine/src/tools/wechat/wx-query.ts` | Engine tool注册，调用Python脚本 |
| features.ts | `C:/Users/24045/.openclaw/engine/src/tools/features.ts` | 注册wechat feature |
| xiaoke.json | `C:/Users/24045/.openclaw/engine/configs/xiaoke.json` | 配置中启用 `"wechat": true` |
| monitor-config.json | `~/.wechat-cache/monitor-config.json` | 监控名单配置 |
| 缓存数据库 | `~/.wechat-cache/MSG0~8.db + MicroMsg.db` | 解密后的SQLite文件 |
| 解密密钥 | `~/.wechat-cache/key.txt` | 缓存的内存提取密钥 |
| cron任务 | cad592d60 | 每3小时巡检 |

## 依赖

- **Python 3.10+** + `pywxdump`（`pip install pywxdump`）
- 微信 PC 端 3.9.12.55 必须运行中（密钥从内存提取）
- wxid: `ccerty_cn`

## 命令

```bash
python3 wx_query.py info                                    # 状态概览
python3 wx_query.py list_groups --active --limit 20         # 活跃群聊
python3 wx_query.py list_chats                              # 私聊列表
python3 wx_query.py history --chat "群名" --limit 10        # 聊天记录
python3 wx_query.py search --keyword "关键词"               # 全局搜索
python3 wx_query.py cron_inspect                            # cron巡检（读配置过滤）
```

## 监控配置 (~/.wechat-cache/monitor-config.json)

```json
{
  "groups": {
    "mode": "all",           // all=全监控 watch=只监控名单 off=关闭
    "watch": [],             // mode=watch时的白名单
    "block": ["广告群1"]     // 黑名单（模糊匹配）
  },
  "dm": {
    "mode": "watch",         // 默认watch+空名单=不读私聊
    "watch": [],             // 要开私聊：改mode="all"或加名单
    "block": []
  },
  "check_minutes": 180      // 巡检时间窗口（分钟）
}
```

## 工作原理

1. 微信运行时密钥在内存中 → `wxdump info`提取32字节AES-256密钥
2. 用密钥解密 `MSG0~8.db`（SQLCipher 4, AES-256-CBC）→ 缓存到 `~/.wechat-cache/`
3. 后续查询直接读缓存（毫秒级），检测源文件mtime变化自动重新解密
4. cron每3小时跑 `cron_inspect` → 读配置过滤 → 群聊/DM分开输出JSON

## 不升级微信

当前版本 3.9.12.55，PyWxDump完美支持。升级后数据库结构可能变化导致密钥提取失败。
