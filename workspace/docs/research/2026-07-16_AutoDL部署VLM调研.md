# AutoDL 部署 VLM 调研报告

> 日期：2026-07-16 | 作者：小柯

## 背景

当前 voice-chat perception 用百炼 API（qwen-vl-plus），走外网延迟 1.7-1.9s。
翀哥希望自部署 VLM 到 AutoDL，降低延迟，同时作为日常聊天模型（glm-5.2 太奢侈）。

## 需求

1. **视觉感知**：替代百炼 qwen-vl-plus，看摄像头画面
2. **日常聊天**：替代 glm-5.2 做轻量对话，省钱
3. **4090 可跑**：AutoDL 单卡 4090（24GB）
4. **部署简单**：不想从头配环境

## 候选模型对比

| 模型 | 参数量 | 显存 | 4090 速度（估计） | 视觉 | 适合场景 |
|------|--------|------|-------------------|------|----------|
| Qwen2.5-VL-7B | 7B | ~16GB | ~100 tokens/s | ✅ | 感知+聊天（推荐） |
| Qwen2.5-VL-3B | 3B | ~8GB | ~200+ tokens/s | ✅ | 极速但聪明度差 |
| Kimi-VL-A3B | 16B MoE (3B活跃) | ~12GB | ~150 tokens/s | ✅ | 又快又聪明（新） |
| gemma-3-4b | 4B | ~8GB | ~180 tokens/s | ✅ | Google出品，轻量 |
| Qwen2.5-7B-Instruct | 7B | ~16GB | ~120 tokens/s | ❌ | 纯文本聊天 |

## 推荐方案

### 首选：Qwen2.5-VL-7B-Instruct + vLLM

**理由：**
- 阿里出品，中文场景最成熟
- 7B 在 4090 上稳定跑，速度够快
- vLLM 一行命令启动，OpenAI 兼容 API
- 支持 image + text 输入，perception 和聊天都能用

**性能预估（vs 百炼 API）：**
| 指标 | 百炼 API（现在） | 自部署 7B（预估） |
|------|------------------|-------------------|
| VLM 延迟 | 1.7-1.9s | 0.5-0.8s |
| 网络 | 外网 | AutoDL 内网 |
| 成本 | 按量计费 | 4090 ~2元/小时 |
| 并发 | 受限 | 完全可控 |

### 备选：Kimi-VL-A3B-Thinking

如果 7B 效果不够好或想更聪明：
- MoE 架构，160亿参数但只激活28亿
- 有 Thinking 版本（带推理链）
- 月之暗面出品，中文好

## 部署步骤

### 1. AutoDL 开机
- 选 4090（24GB）单卡
- 镜像：PyTorch 2.1.0 + CUDA 11.8（AutoDL 自带）

### 2. 安装 vLLM
```bash
pip install vllm
```

### 3. 下载模型
```bash
# ModelScope（国内快）
pip install modelscope
modelscope download --model="Qwen/Qwen2.5-VL-7B-Instruct" --local_dir /root/autodl-tmp/Qwen2.5-VL-7B-Instruct
```

### 4. 启动服务
```bash
vllm serve /root/autodl-tmp/Qwen2.5-VL-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 4096 \
  --max-num-seqs 8 \
  --gpu-memory-utilization 0.85 \
  --enforce-eager \
  --trust-remote-code
```

### 5. 验证
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2.5-VL-7B-Instruct",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 6. 接入 voice-chat

修改 `perception.py`，把百炼 API 调用改为自部署 vLLM 端点：
- API URL: `http://<autodl-ip>:8000/v1/chat/completions`
- 请求格式：OpenAI 兼容（image_url + text）
- 不需要 API Key（或设个假的）

## 成本分析

| 方案 | 费用 | 说明 |
|------|------|------|
| 百炼 qwen-vl-plus | 0.003元/千tokens | 按量，量大了贵 |
| AutoDL 4090 | ~2元/小时 | 按需开关，不用就关 |
| AutoDL 4090 包日 | ~15-20元/天 | 长期用划算 |

**结论：** 如果 perception 每天跑 8 小时以上，自部署更便宜。偶尔用的话百炼 API 更省。

## 风险与注意事项

1. **模型下载**：7B 约 15GB，AutoDL 内网从 ModelScope 下载快（几分钟）
2. **冷启动**：vLLM 首次加载模型约 30-60s
3. **AutoDL 端口**：需要用 AutoDL 的端口映射，不是直接 8000
4. **显存**：7B bf16 约 16GB，4090（24GB）有富余
5. **量化选项**：如果显存紧张，可用 AWQ 4-bit 量化版（~8GB）

## 下一步

1. 翀哥回来开 AutoDL 4090 实例
2. 部署 Qwen2.5-VL-7B + vLLM
3. 压测延迟（对比百炼 API）
4. 接入 perception.py
5. 如果效果好，考虑同时替代聊天模型
