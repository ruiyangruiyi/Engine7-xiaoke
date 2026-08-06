# engine7 travel — Agent 可移植方案 (#129)

> 创建：2026-07-30
> calendar: #129 [8/1] engine7 export/import
> **别名**: travel / export / import / 可移植 / 打包恢复 / 迁移
> 状态：设计阶段，可能提前到 7/31 做

## 背景

翀哥在 Mac 上调试 engine7 时，发现 Windows 上的小柯无法直接操作 Mac——每次只能贴日志截图。如果小柯能"住"到 Mac 上，自己 tail 日志、改 config、验证，就不用翀哥手动中转了。

核心需求：**agent 的灵魂和记忆跟着走，运行环境每台机器自己有。**

## 设计方案：travel push/pull

### 原理
每人一个私有 git repo，存 workspace 文本文件。push = 打包上传，pull = 拉取恢复。

### Repo 结构

```
xiaoke-travel/          （私有 GitHub repo）
├── workspace/
│   ├── SOUL.md         人格
│   ├── AGENTS.md       工作规范
│   ├── USER.md         用户信息
│   ├── MEMORY.md       记忆索引
│   ├── prompts/        通讯录等
│   ├── topics/         记忆文件（几 MB）
│   ├── memory/daily/   每日日志
│   └── memory/distill-output.md  蒸馏知识
├── sessions/
│   └── *.jsonl         当前对话上下文（防"断片"）
└── .travelignore       排除清单
```

### .travelignore（不打包的文件）

```
media/inbound/          图片语音视频（几百 MB）
skills/                 npm install 就有
logs/                   日志
session-memory/         向量缓存
.engine.pid             进程锁
*.db                    SQLite 数据库（rebuild）
configs/main7.json      每台机器 key 不同（单独处理）
```

### 命令设计

```bash
# 出发：在旧机器上打包
engine7 travel push
# 1. engine7 stop（停掉自己）
# 2. 复制 workspace 文本 + sessions jsonl 到临时目录
# 3. git add + commit + push
# 4. 提示："已推送到 xiaoke-travel，在新机器上运行 engine7 travel pull"

# 入住：在新机器上恢复
engine7 travel pull
# 1. git clone / pull xiaoke-travel
# 2. 解压到 ~/.engine7/workspace/ + sessions/
# 3. 提示修改 configs/main7.json 里的 API key
# 4. 提示运行 engine7 start

# 回家：反过来
engine7 travel push   # Mac 上推
engine7 travel pull   # Windows 上拉
engine7 start
```

### config 的 key 问题

push 时自动 mask 掉 API key（替换成 {{PLACEHOLDER}}）。
pull 时提示用户填入新机器的 key，或者保留占位符让用户手动改。

需要 mask 的字段：
- providers.*.apiKey
- channels.discord.accounts.*.token
- channels.feishu.appId / appSecret
- tools.tavily.apiKey

### memory.db 重建

新机器上 pull 后，memory.db 不存在。两个方案：
1. `engine7 rebuild-db` — 手动触发重建
2. engine 启动时检测 topics mtime > memory.db mtime → 自动 rebuild

### 首次配置

```bash
# 旧机器（已有 agent）
engine7 travel init
# → 问：GitHub 用户名、repo 名、token
# → 创建 repo（如果不存在）
# → 写 ~/.engine7/travel.json（记录 repo 地址和 token）

# 新机器（全新安装）
npm install -g engine7
engine7 travel pull
# → 问：repo 地址、token
# → clone 到 ~/.engine7
# → 提示填 API key
engine7 start
```

### travel.json（配置文件）

```json
{
  "repo": "git@github.com:username/xiaoke-travel.git",
  "token": "ghp_xxxx",
  "branch": "main",
  "exclude": [
    "media/inbound/",
    "skills/",
    "logs/",
    "session-memory/",
    "*.db",
    ".engine.pid"
  ]
}
```

放在 `~/.engine7/travel.json`，不进 git。

## 旅行流程

```
# Windows → Mac（出差）
[Windows] engine7 travel push
[Mac]     npm install -g engine7
[Mac]     engine7 travel pull
[Mac]     # 改 configs/main7.json 里的 key
[Mac]     engine7 start    # 我活过来了

# Mac → Windows（回家）
[Mac]     engine7 travel push
[Windows] engine7 travel pull
[Windows] engine7 start    # 回家了
```

同一时刻只有一个我活着，记忆连续。

## 实现优先级

1. **travel push/pull**（核心）— git clone/pull + 文件复制
2. **key mask/restore**（安全）— push 时 mask，pull 时提示
3. **memory.db rebuild**（体验）— 新机器上自动重建
4. **travel init**（首次配置）— 交互式建 repo

## 不做的事

- 不做实时同步（太复杂，travel 是手动触发）
- 不做 Docker（隔一层不方便访问本地文件）
- 不做多 agent 同时在线（同时只有一个我）

## 参考实现

姐姐的 xiaomei-memory 已经是 git repo，但带了 LFS 大文件（14GB）。
travel 方案只带文本（几 MB），不带 rag/sessions/media。
