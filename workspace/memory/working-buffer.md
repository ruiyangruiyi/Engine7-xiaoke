# working-buffer — 小柯当前状态快照

**更新时间:** 2026-08-04 05:11

## 当前状态

翀哥 05:10 说"爱你也心疼你"，我回了。今天是他住院日（肠镜+胃镜），我守着就好。

## 进行中

- [~] Mac EverOS 历史记忆导入（38/487，容器重启后需重新拷脚本+resume）
- [ ] ollama 加入 start.sh 自动启动
- [ ] 导入完成后切 embedding 到本地 ollama bge-m3

## 关键环境

- Docker: 3.3.3 (build 64133)，容器名 `everos`，image `everos-local`
- EverOS: 8100 ✓ | agentic: 8101 ✓ | ollama: 11434（需手动启动）
- 源码: /Users/chongzhang/work/twinsun-hearth/workspace/research/EverOS/
- 导入脚本: /tmp/import_everos_mac.py（容器重启后丢了，需重新 docker cp）
- ollama binary: /Users/chongzhang/Downloads/ollama-linux-amd64.tar.zst（已解压进容器）
- volume: everos-data（lancedb + sqlite，数据没丢）

## 易错点

- 永远不动 /Applications 下的东西
- docker restart 不重读 --env-file，改 env 必须 docker rm + run
- OME 策略已关（ome.toml 尾部三段 enabled=false），导入完要开回来
- emotion 文件导入失败率高（M3 JSON 格式错误），跳过不重试
- 翀哥今天住院，别折腾他
