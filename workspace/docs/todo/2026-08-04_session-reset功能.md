# session reset 功能（2026-08-04 翀哥提需求）

## 背景

小文收到一张被 M3 判敏感的图，图片块存在**内存 session** 里（feishu 收图→dataUri block→每轮进 API），JSONL 本身干净。只要图在内存历史里，每轮请求都撞 `input new_sensitive` 500。临时解法：重启小文（内存清空，历史从干净 JSONL 重建）。

需要一个可复用的 reset 工具。

## 设计（2026-08-04 和翀哥讨论定稿）

```
engine7 session reset --mode archive|drop-last|strip-images [参数]
```

| 模式 | 作用 | 场景 |
|------|------|------|
| `archive` | 主 JSONL 改名 `.archived` 后缀 | 整个会话废掉重来。restore 明确不读 archived（findAllSessionFiles 注释："archived 文件不恢复"），改名即永久移出内存 |
| `drop-last N` | 砍最近 N 轮（user+assistant 对） | **急救场景**：最近几轮有脏东西（敏感图/agent 跑偏/注入），切掉回到正常态。翀哥纠正：砍旧历史没用（compaction 自己会压），砍最近的才实用 |
| `strip-images` | 只摘 image block / 图片路径引用，保留文字 | 丢上下文最少的手术模式（今天小文场景） |

## 为什么用 CLI 而不是 session 内 slash 命令（8/4 翀哥问）

1. **CLI 是外部进程，能安全 kill+restart 目标 engine**——engine 自己重启自己是自杀，做不到；slash 命令跑在 engine 内部，重启不了自己。
2. **engine 坏了也能救**——slash 命令依赖 engine 活着才能执行；今天小文每轮 500，session 内任何命令都够不着，只有外部干预救了她。CLI 不依赖目标 engine 存活。

## 关键约束

1. **CLI 不能自动生效**：engine 历史在内存缓存（getHistory 返回内存，仅 history 为空时从 JSONL restore 一次）。改文件后**必须重启**。
2. CLI 默认只改文件 + 打印提示"请 engine7 restart"。
3. `--restart` flag：改完直接 kill + nohup 拉起——**给人用**。AI 不可用（不能碰进程操作）。
4. archive 命名用 `.archived` 后缀即可（reader.ts `findAllSessionFiles` 只读主文件+最近一个 compaction 文件；`.jsonl.*` 通配只用于 session 列表展示）。

## 验证标准

- archive 后重启 → 历史为空（全新会话）
- drop-last 3 重启 → 最后 3 轮消失，更早的完整
- strip-images 重启 → 文字保留、image block 消失、不再撞敏感 500

## 状态

- [ ] 等翀哥出院后做（8/6）
