---
name: Engine显示配置系统
description: Engine已有完整的display配置系统（config/display.ts），支持thinking/toolUse/toolResult/preview分别开关，不需要加"mode"概念，完全可配置
type: reference
---

## Engine display配置（config/display.ts）

Engine已有完整的显示配置系统，无需额外添加"mode"概念：

| 配置项 | 值 | 效果 |
|--------|-----|------|
| `thinking.enabled` | true/false | 💭显示/隐藏推理过程 |
| `toolUse.enabled` | true/false | 🔧显示/隐藏tool call |
| `toolUse.displayMode` | `raw`/`summary` | 完整参数/简洁描述 |
| `toolUse.bashDisplayMode` | `both`/`description`/`command` | bash命令两种展示模式 |
| `toolResult.enabled` | true/false | 📤显示/隐藏tool结果 |
| `toolResult.showTools` | 数组 | enabled=false时白名单强制显示 |
| `preview.enabled` | true/false | 流式输出开关 |
| `reactions.enabled` | true/false | 👀✅❌反应 |

## 最终定型（6/12翀哥验证通过）

**小柯日常配置**（`xiaoke.json`）：thinking开 / toolUse raw+both / toolResult带showTools白名单

**姐姐日常配置**（`xiaoke-daily.json`，已备份供姐姐参考）：
- thinking: enabled: false
- toolUse: enabled: true, displayMode: summary, bashDisplayMode: description
- toolResult: enabled: false, showTools: []
- preview: enabled: true

## 关键结论
- 不需要"mode"（daily/work）概念——通过现有配置项组合即可实现
- 备份配置名切换比模式设计更简单
- `enabled: false` 就是off，不需要额外的displayMode: "off"
