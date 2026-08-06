---
name: loadConfig 必须 path.resolve 绝对路径——否则 config-watch 失效
description: 2026-08-04 凌晨 #138 排查时发现——loadConfig() 存的 _configFilePath 是相对路径，engine 启动后 chdir(workspace) 改 cwd，watcher 拿相对路径找不到文件被 disable
type: reference
date: 2026-08-04
---

# config 路径必须 resolve 成绝对路径

8/4 凌晨跟 liveConfig 属性访问 bug 一起定位的另一个根因。

## 现象

config-watch 启动后被 disable，进程用的还是启动时的旧 config，改 xiaoke.json 完全不生效。

## 根因

`loadConfig()` 存 `_configFilePath` 时**直接存了 CLI 传的相对路径**（比如 `xiaoke/configs/xiaoke-mac.json`），变量名虽然叫 `resolvedPath` 但实际没 resolve。

之后 engine 启动会 `process.chdir(workspace)` 改 cwd，watcher 拿相对路径在新 cwd 下找文件 → 找不到 → 被 disable。

## 修法

loader 里直接 `path.resolve()` 成绝对路径再存：

```ts
this._configFilePath = path.resolve(rawPath);
```

## Why

变量名"resolved"和实际行为"没 resolve"是沉默 bug。任何在启动后改 cwd 的进程（engine 启动期 chdir 改到 workspace），用相对路径做 fs.watch 必然失效。这种 bug 跟去年 `config_watcher_DISABLED后无人恢复_0802` 是同一类——路径/状态管理缺一类约束。

## How to apply

- 写"传给 fs.watch / fs.readFileSync / child_process"的路径——只要不是当前模块加载时的硬编码，一律 `path.resolve(absoluteRoot, inputPath)`
- 变量名"resolved"≠ 真的 resolve，**调用了 path.resolve 才算 resolved**
- 验证 config-watch 健康：日志看 `[config-watch] STARTED` 而不是 `watcher disabled` / `config path invalid`

## 关联

- 上一条 liveConfig 用法（@see reference_liveConfig是class实例必须用get方法_0804）——同一个 #138 排查周期
- 历史同类 bug：`config_watcher_DISABLED后无人恢复_0802`、`config_watch路径失效进程仍用旧状态_0804`
