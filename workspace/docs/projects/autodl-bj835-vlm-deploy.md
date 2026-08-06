# AutoDL bj835 — Qwen2.5-VL-7B + vLLM 部署过程

> 2026-07-16 部署完成

## 机器信息

- **AutoDL 实例**: bj835
- **GPU**: 5090
- **数据盘**: 大容量（可放模型权重）
- **系统**: Linux

## 部署步骤

### 1. 安装 vLLM

```bash
pip install vllm
```

**坑1**: nvrtc 缺失
```
ImportError: libnvrtc.so
```
**解决**: 安装 nvidia-cuda-nvrtc-cu12 或手动设置 LD_LIBRARY_PATH

**坑2**: ninja 编译依赖
```
Ninja is required to build
```
**解决**: `pip install ninja`

### 2. 下载模型

```bash
# Qwen2.5-VL-7B ~15GB
# 存到数据盘
```

下载耗时约 30 分钟。

### 3. 启动 vLLM 服务

```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-VL-7B-Instruct \
  --trust-remote-code \
  --port 8000 \
  --host 0.0.0.0
```

### 4. 验证 API

```bash
# 纯文本
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-VL-7B-Instruct","messages":[{"role":"user","content":"你好"}]}'

# 带图片
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-VL-7B-Instruct","messages":[{"role":"user","content":[{"type":"text","text":"描述这张图"},{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,xxx"}}]}]}'
```

## 延迟对比

| 场景 | 本地 vLLM (5090) | 百炼 API (qwen-vl-plus) | 提升 |
|------|-----------------|------------------------|------|
| 纯文本 | 318ms | 1700ms | **5.3x** |
| 带图片 | 585ms | 1900ms | **3.2x** |

## 外部访问

- AutoDL 内部端口: 8000
- 外部映射: AutoDL 控制台 → 实例详情 → 「自定义服务」获取映射地址
- 格式: `https://connect.xxx.seetacloud.com`

## 待办

- [ ] 获取外部映射地址
- [ ] perception.py 切换到本地 vLLM 端点
- [ ] 验证 voice-chat 感知延迟下降
