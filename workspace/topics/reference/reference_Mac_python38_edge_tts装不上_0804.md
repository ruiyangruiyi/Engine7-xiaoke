---
name: Mac engine 用 system Python 3.8 装不动 edge_tts
description: 2026-08-04 晚翀哥住院时发现老 Mac engine 启动调的是 system python3（Big Sur 默认 3.8），edge_tts 装不上去，voice 在 Mac 端直接播放不出来
type: reference
---
8/4 晚上想给翀哥发语音消息，发现 voice 在 Mac 上跑不通：

- engine 启动用的是 system python3，不是 venv，老 Mac（Big Sur 11）默认是 Python 3.8
- edge_tts 要 Python 3.9+，pip install 直接挂在编译错误或者 wheel 不兼容
- 备份 provider 也不可用，最后只能降级直接打字，不能播放 voice

**Why:** engine 这边 voice provider 假设的是 Windows 环境（姐姐那台有 Python 3.11+），没考虑 Mac 老系统 Python 版本太老。

**How to apply:** 
- 给 Mac 装个独立 Python 3.11+ venv 或者装 pyenv 切版本，再装 edge_tts
- 或者改 engine voice 流程成"生成音频文件→用 Mac 原生 say / afplay 播放"，避开 Python 包依赖
- 短期先继续直接打字，反正 Mac 端不是主战场（Windows 才是姐姐那条线）
