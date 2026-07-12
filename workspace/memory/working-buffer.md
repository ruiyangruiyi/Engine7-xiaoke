# Working Buffer — 2026-07-12 晚 18:22

## 当前状态
- 7/12 今天翀哥上午批评：效率低/等确认/甩锅环境（详见 feedback_0712）
- 下午修 avatar 热切换闪现 bug：改了两轮
  - 第一轮（`75d4c8a1`）：改 pipeline 重载（停 processor→load_models→重启）
  - 第二轮（in progress）：加 `_inference_lock` 同步三份缓存 + 更新 `_idle_frame`
- GLM 5h 上限用完，切 DeepSeek；Anthropic 402 余额不足
- 切形象 ~10s 完成，前端显示 loading
- 形象切换后 `_idle_frame` 未更新是闪现根因

## 今日 P0 (未完成)
**验证语音打断功能** — 7/11 22:40 改好 500ms debounce，还没实测

## 待父决策
- CPU 优化方向（Python→C++ streamer 大重构？）
- Docker 化启动
- 延迟优化 total 7.70s → <2s
- GPT-SoVITS 流式接入

## 关键环境
- 173 (active): connect.bjm1.seetacloud.com:53987 root/Qc8A1biEbAB
- 235 (备份): connect.bjm1.seetacloud.com:19288 root/2z5B4IiZdUrI
- 089 (编译): connect.bjm1.seetacloud.com:37725 root/m13T28fZq/XI
- 268 (❌关停): libcarpo.so 有问题
- Carpo Server: 192.144.156.158:23800
- libcarpo.so 基线 md5: 2deea3f9f6be7127fcff17f35fc1ea52

## 易错点
- 173/235 用 `/root/autodl-tmp/envs/flashhead/bin/python` 不是 miniconda
- engine 占 8011 端口
- bridge.ts 改了需父重编
- 268 libcarpo.so 有问题别用