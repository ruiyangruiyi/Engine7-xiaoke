# cc-connect npm Wrapper 版本检查风险

## 问题描述

npm全局安装的cc-connect (`npm install -g cc-connect`) 不是纯粹的Go二进制，而是有wrapper层：

```
cc-connect.cmd → run.js → cc-connect.exe
```

**run.js会检查exe版本** — 对比package.json里的版本号和实际exe的版本号。如果不匹配，触发自动重装。

## 问题代码位置

`node_modules/cc-connect/run.js` 中的 `needsReinstall()` 函数，会在检测到版本不匹配时调用 `install.js` 重新下载并覆盖 `bin/cc-connect.exe`。

## 风险

小柯修改的 `allow_bots=true` 版exe（30M）会被覆盖回官方旧版（21M），导致：
1. `allow_bots` 配置项消失（官方版不支持）
2. 跨bot通信再次中断

## 症状

启动cc-connect时如果看到类似输出，说明自动重装触发了：
```
Binary missing or outdated, installing...
```

## 临时解决方案

绕过wrapper，直接运行exe：
```
C:\Users\24045\AppData\Roaming\npm\node_modules\cc-connect\bin\cc-connect.exe
```

## 根本解决方案

1. **不用npm安装** — 直接下载Go编译结果或从release页面拿二进制
2. **修改run.js** — 把版本检查逻辑注释掉或跳过
3. **固定版本号** — 让自定义exe的版本号与package.json一致

## 教训

修改第三方npm包的二进制后，npm upgrade/update 可能触发覆盖。修改前先确认是否有wrapper层以及版本检查机制。
