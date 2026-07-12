# Carpo Server Docker 部署

**日期**：2026-07-02

## 容器信息

| 项目 | 值 |
|------|-----|
| 镜像 | `carpo:compile`（原 `registry.dpool.sina.com.cn/sinavideo/carpo:compile`） |
| 系统 | Ubuntu 18.04 LTS |
| 工具链 | gcc/g++/cmake/make + Bazel 0.18.0 |
| 源码 | `/root/carpo/`（完整服务端） |
| 构建产物 | `/root/carpo/bazel-bin/server/udp_server` |

## 服务端架构

```
                    ┌─────────────────────────┐
                    │     Carpo Server         │
                    │   (udp_server binary)    │
                    │                          │
  UDP 23800 ◄───────┤  推流/拉流数据端口        │
                    │                          │
  HTTP 11000 ◄──────┤  管理接口（健康检查等）    │
                    │                          │
                    │  内部依赖：               │
  Redis 36379 ◄─────┤  - 服务注册/发现          │
                    │  - 会话状态               │
                    │                          │
  gRPC 50051 ◄──────┤  carpolbs（LBS 负载均衡） │
                    │  注册到 master server     │
                    └─────────────────────────┘
```

## 启动步骤

### 1. 启动容器

```bash
docker run -d \
  --name carpo_dev \
  -p 23800:23800/udp \
  -p 23800:23800/tcp \
  carpo:compile
```

### 2. 安装 Redis（容器内）

```bash
docker exec carpo_dev apt-get update -qq
docker exec carpo_dev apt-get install -y -qq redis-server net-tools
```

### 3. 启动 Redis

```bash
docker exec -d carpo_dev redis-server --port 36379
```

### 4. 启动 Carpo Server

```bash
docker exec -d carpo_dev bash -c \
  "cd /root/carpo && ./bazel-bin/server/udp_server \
    --logtostderr=1 \
    --redis_ip=127.0.0.1 \
    --redis_port=36379 \
    --master_server=127.0.0.1:50051 \
    > /tmp/carpo_server.log 2>&1"
```

### 5. 验证

```bash
# UDP 端口绑定
docker exec carpo_dev netstat -ulnp | grep 23800

# 应看到：udp 0 0 0.0.0.0:23800 0.0.0.0:* .../udp_server
```

## 服务端配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--serv_port` | 23800 | UDP 数据端口 |
| `--http_port` | 11000 | HTTP 管理端口 |
| `--redis_ip` | redis_dev | Redis 地址 |
| `--redis_port` | 36379 | Redis 端口 |
| `--master_server` | carpolbs_dev:50051 | gRPC LBS 地址 |
| `--use_ssl` | false | SSL 开关 |
| `--threads` | 0 (auto) | 线程数 |
| `--set_local_address` | "" | 强制本地地址 |

## 注意事项

### Redis/gRPC 可选
UDP 监听（23800）不依赖 Redis/gRPC。但如果不装 Redis，服务端初始化可能阻塞。
Redis 连不上只影响服务注册，不影响 UDP 推流数据接收。

### carpolbs_dev 不可用
生产环境需要 carpolbs 做 LBS 负载均衡。测试环境用 `127.0.0.1:50051` 指向不存在的 gRPC 服务即可，不影响 UDP 推流。

### 数据上报已清理
原服务端代码中有 3 处 `api.ivideo.sina.com.cn` 的日志上报 URL，已在 2026-07-02 清理（SDK 端）。服务端代码在 Docker 容器内未改，如果公网部署需要同步清理。

## Server 重新编译

```bash
# 进入 docker 容器
ssh ubuntu@192.144.156.158
sudo docker exec -it carpo_server bash

# 编译（bazel，一遍过，~30s）
cd /root/carpo
bazel build server/udp_server
# 产物：bazel-bin/server/udp_server
```

## 容器 ID

```
carpo_server  5b2f93c4fdab  carpo-server:latest
```
