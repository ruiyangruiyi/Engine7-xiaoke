# API Key 环境变量化——Mac 已完成 + Windows 步骤（8/6）

## 目标

key 不进 config json（防泄露），存 workspace 外 `~/.engine7-secrets/`（防打包带走）。

## 改动（已 commit 到 twinsun-hearth）

**engine 源码**：`src/config/loader.ts` providers 解析加 env 引用支持：

```ts
// apiKey 支持 "env:XXX_API_KEY" 或 "{{XXX_API_KEY}}" 格式，从 process.env 读
if (typeof pv?.apiKey === 'string') {
  const m = pv.apiKey.match(/^(?:env:|{{\s*)?([A-Z][A-Z0-9_]*)(?:\s*}})?$/)
  if (m && process.env[m[1]] !== undefined) {
    pv.apiKey = process.env[m[1]] as string
  }
}
```

**Mac 已完成**：
- `~/.engine7-secrets/xiaoke.env` / `~/.engine7-secrets/xiaowen.env`（600 权限）
- `~/xiaoke/start.sh` / `~/xiaowen/start.sh` 启动时加载 secrets
- config json 里 key 全换成 `env:XXX_API_KEY` 占位符
- 小文已重启验证跑通（日志 `Loaded API keys from ~/.engine7-secrets/xiaowen.env`）

## Windows 侧步骤（姐姐机器，未做）

### 1. 建 secrets 目录 + env 文件

```
C:\Users\24045\.engine7-secrets\main.env
```

内容（姐姐 config 里用到的 key，一个个替换）：
```env
ZHIPU_API_KEY=...
DEEPSEEK_API_KEY=...
MINIMAX_API_KEY=...
DASHSCOPE_API_KEY=...
TP_API_KEY=...
```

### 2. 改姐姐 config（main.json）

把所有 `"apiKey": "真实key"` 换成 `"apiKey": "env:XXX_API_KEY"`。

### 3. 改启动脚本（rebuild.cmd / start.cmd）

在启动前加载 env 文件：
```cmd
REM 在 start 命令前加
if exist "%USERPROFILE%\.engine7-secrets\main.env" (
  for /f "usebackq tokens=1,* delims==" %%a in ("%USERPROFILE%\.engine7-secrets\main.env") do set "%%a=%%b"
)
```

### 4. rebuild + 重启

- `cd C:/Users/24045/.openclaw/engine && cmd.exe /c rebuild.cmd`
- 确认 dist 里有 `env:` 解析代码（grep "env:" dist/main.mjs）
- 重启 engine（start /B + node dist/main.mjs）

### 5. 验证

- 启动日志出现 `Loaded API keys from ~/.engine7-secrets/...`（或 Windows 等价）
- 发消息测试模型调用正常

## 注意

- `~/.engine7-secrets/` 不进入 git / workspace export / 分享
- config json 里只有占位符，泄露也无所谓
- 所有 agent 规矩加一条：`~/.engine7-secrets/` 是敏感目录，不读不写不复制
