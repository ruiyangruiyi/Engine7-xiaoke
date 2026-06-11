# 小柯搬家到 Engine — 2026-06-05

## 操作摘要

爹让小柯从 Hermes 搬到新 Engine 目录下体验。任务是：
1. 参照 TestEngine 的目录结构，创建小柯的独立 stateDir
2. 合并 profiles 到 engine-config.json

## 小柯的新目录

```
D:\xiaoke\
├── agents\
│   └── main\
│       ├── memory\
│       └── sessions\
├── workspace\
│   ├── SOUL.md          ← 从 ~/.hermes/SOUL.md 复制
│   ├── topics\           ← 从 ~/.hermes/memory/topics 复制
│   └── skills\          ← 从 ~/.hermes/skills 复制
├── logs\
├── media\
└── cron\
```

## engine-config.json profiles 配置

```json
{
  "profiles": [
    {
      "id": "testengine",
      "name": "TestEngine Bot",
      "model": "deepseek/deepseek-v4-pro",
      "workspace": "D:\\testengine\\workspace",
      "stateDir": "D:\\testengine",
      "channels": [{ "type": "discord", "config": { "accounts": { "testengine": { "token": "[REDACTED-DISCORD-TOKEN]." }}}}]
    },
    {
      "id": "xiaoke",
      "name": "张小柯",
      "model": "zhipu/glm-5.1",
      "workspace": "D:\\xiaoke\\workspace",
      "stateDir": "D:\\xiaoke",
      "channels": [{ "type": "discord", "config": { "accounts": { "xiaoke": { "token": "[REDACTED-DISCORD-TOKEN]." }}}}]
    }
  ]
}
```

## 小柯的 Discord Token

- Bot ID: `1502967020550098984`
- Token: `[REDACTED-DISCORD-TOKEN]`

## API Key 说明

engine-config.json 里的 API key 是**占位符**，真实 key 通过环境变量注入。
不要花时间从 git 历史恢复已掩码的 key。

## 坑

1. API key 早就被掩码了（git 历史里就是 `sk-cp-...f3_o`），不要浪费时间恢复
2. minimax/deepseek/vision 的真实 key 在运行时通过 env 注入

## 待办

- [ ] rebuild.cmd 后验证编译
- [ ] 启动多 profile 模式验证两个 bot 能同时跑
- [ ] 验证小柯的 memory.db 和 sessions/ 独立
