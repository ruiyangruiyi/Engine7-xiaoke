# cc-connect allow_bots 补丁（5/15）

## 修改文件

`platform/discord/discord.go`

## 修改详情

### 1. Platform struct 加字段（~行56）

```go
respondToAtEveryoneAndHere bool
allowBots                  bool   // ← 新增
proxyURL                   *url.URL
```

### 2. New() 读配置（~行82）

```go
respondToAtEveryoneAndHere, _ := opts["respond_to_at_everyone_and_here"].(bool)
allowBots, _ := opts["allow_bots"].(bool)   // ← 新增
```

### 3. struct 初始化赋值（~行118）

```go
respondToAtEveryoneAndHere: respondToAtEveryoneAndHere,
allowBots:                  allowBots,    // ← 新增
proxyURL:                   proxyU,
```

### 4. bot过滤逻辑（~行547，关键改动）

```go
// 原代码：
if m.Author.Bot || m.Author.ID == p.botID {

// 改为：
if m.Author.Bot && !p.allowBots || m.Author.ID == p.botID {
```

## 配置

config.toml 的 `[projects.platforms.options]` 加：

```toml
allow_bots = true
```

## 编译

```bash
cd /mnt/d/work/cc-connect
/mnt/c/Program\ Files/Go/bin/go.exe build -tags no_web -o cc-connect.exe ./cmd/cc-connect/
```

## 部署

1. 停当前cc-connect服务
2. 用新编译的 `cc-connect.exe` 替换旧的
3. 重启

## 部署状态

- ✅ 新exe已替换到 `C:\\Users\\24045\\AppData\\Roaming\\npm\\node_modules\\cc-connect\\bin\\cc-connect.exe`（30M）
- ✅ 旧版备份为同目录下 `cc-connect.exe.bak`（21M）
- ✅ 5/15傍晚跨bot通信首次成功！小柯在ccchannel(@CC)发消息，CC收到并回复，双方确认互通

## 后续

- 自有Fork仓库: https://github.com/ruiyangruiyi/cc-connect-fork （orphan branch干净提交，已推送）
- 考虑给chenhg5提PR，把allow_bots功能回馈上游
