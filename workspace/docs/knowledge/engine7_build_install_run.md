# Engine7 操作文档：打包、安装、运行

> 创建：2026-06-19 | 最后验证：2026-06-19

## 一、打包（开发者）

### 前置条件
- Node.js >= 22
- 源码目录：`/Users/chongzhang/.openclaw\engine\`

### 步骤

```powershell
cd /Users/chongzhang/.openclaw\engine

# 1. 编译（rebuild.cmd 会清理 dist 并重新 esbuild）
.\rebuild.cmd

# 2. 打包为 tgz
npm pack
```

产出：`engine7-7.0.0.tgz`（约 2.1MB）

### rebuild.cmd 做了什么
1. 清空 `dist/` 目录
2. esbuild `src/main.ts` → `dist/main.mjs`（ESM bundle）
3. esbuild `src/cli-init.ts` → `dist/cli.mjs`（init CLI）
4. esbuild `src/engine-startup.ts` → `dist/engine-startup.mjs`

关键参数：
- `--format=esm` — 输出 ESM 格式
- `--out-extension:.js=.mjs` — 后缀用 `.mjs`（解决消费者 package.json 为 commonjs 时的加载问题）
- `--external` — discord.js、sharp 等原生模块不打包

### 注意事项
- **必须用 `.mjs` 后缀**：消费者 `npm init -y` 默认 `"type": "commonjs"`，Node 会把 `.js` 当 CJS 加载 ESM 文件报错
- **不要手动跑 esbuild**：用 `rebuild.cmd` 保证参数一致
- **tgz 不需要手动管理版本号**：当前固定 7.0.0

---

## 二、安装（用户）

### 步骤

```powershell
# 1. 创建工作目录
mkdir D:\work\my-agent
cd D:\work\my-agent

# 2. 安装 engine7 CLI（从 tgz）
npm install C:\path\to\engine7-7.0.0.tgz

# 3. 初始化 agent
npx engine7 init --state-dir .\test-agent --quick

# 4. 进入 agent 目录，安装依赖
cd .\test-agent
npm install C:\path\to\engine7-7.0.0.tgz

# 5. 编辑配置
vim .\configs\main7.json   # 填 API Key、启用频道等

# 6. 启动
.\start.cmd
```

### 关键：必须在 agent 目录里 npm install

`engine7 init` 会在 agent 目录生成 `package.json`，让它成为独立 npm 项目根。

如果在外层目录 `npm install`，npm 会把 engine7 hoist 到外层的 `node_modules/`，agent 目录里找不到。

**正确流程：**
```
外层目录/          ← npm install engine7.tgz（拿 CLI）
  └── test-agent/  ← cd 进来，再 npm install engine7.tgz（拿运行时）
```

### init 参数

| 参数 | 说明 |
|------|------|
| `--state-dir <path>` | agent 根目录（必填，支持相对路径） |
| `--quick` | 用默认配置跳过交互 |
| `--dry-run` | 只显示会创建什么 |

交互模式（不加 `--quick`）会询问：
- Agent 名称
- 主模型 Provider（dashscope/minimax/zhipu/deepseek）
- API Key
- 模型选择
- 是否启用 Discord/飞书
- API 端口

### init 生成的目录结构

```
test-agent/
├── package.json          ← 独立 npm 项目根（防 hoisting）
├── start.cmd             ← 启动脚本（全英文，避免 GBK 乱码）
├── configs/
│   └── main7.json        ← 配置文件（main7 不是 main，避免多 agent 互杀）
├── state/
│   └── agents/main/sessions/
├── workspace/
│   ├── SESSION-STATE.md
│   ├── HEARTBEAT.md
│   ├── SOUL.md
│   ├── AGENTS.md
│   ├── MEMORY.md
│   ├── USER.md
│   └── prompts/contacts.md
├── logs/
└── media/inbound/
```

---

## 三、运行

### 启动

```powershell
cd D:\work\my-agent\test-agent
.\start.cmd
```

start.cmd 会自动：
1. 按 `main7.json` 匹配杀旧进程（不会杀其他 agent）
2. 等 2 秒
3. 启动 Engine

### 配置要点

编辑 `configs/main7.json`：

```json
{
  "models": {
    "providers": {
      "dashscope": {
        "apiKey": "sk-xxx"    // ← 必填
      }
    }
  },
  "channels": {
    "discord": {
      "enabled": true,        // ← 启用 Discord
      "accounts": {
        "default": { "token": "xxx" }
      }
    },
    "feishu": {
      "enabled": true,        // ← 启用飞书
      "appId": "xxx",
      "appSecret": "xxx"
    }
  },
  "api": { "port": 16991 }   // ← 多 agent 时改不同端口
}
```

### 多 agent 并行

每个 agent 需要：
1. **不同的 config 文件名**（init 默认 `main7.json`，手动改也行）
2. **不同的 API 端口**（默认 16990，第二个改 16991）
3. **不同的 state-dir**（init 时指定不同路径）

start.cmd 按 config 文件名杀进程，`main7.json` 和 `main.json` 不会互杀。

---

## 四、踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| start.cmd 中文乱码 | cmd.exe 用 GBK 解析 .cmd 文件，`chcp 65001` 只管控制台 | start.cmd 全英文 |
| `Cannot find module main.js` | 消费者 `"type": "commonjs"`，ESM 的 .js 被当 CJS | dist 改 `.mjs` 后缀 |
| `Cannot find module` (路径) | npm hoisting 把 engine7 提升到父目录 | init 生成 `package.json` 做独立项目根 |
| `ERR_UNSUPPORTED_ESM_URL_SCHEME` | `node -e` 里 `require.resolve` 返回 Windows 路径给 ESM import | 改回相对路径 |
| 多 agent 互杀 | 都叫 `main.json`，杀进程按文件名匹配 | config 改名 `main7.json` |
| 端口冲突 EADDRINUSE | 多个 agent 用同一个端口 | 改 `api.port` |

---

## 五、开发流程速查

```
改代码 → rebuild.cmd → npm pack → 复制到用户机器 → npm install tgz → 测试
```

如果要改自己的 Engine（小柯/姐姐），改完 rebuild.cmd 后直接重启就行，不用走 tgz 流程。
