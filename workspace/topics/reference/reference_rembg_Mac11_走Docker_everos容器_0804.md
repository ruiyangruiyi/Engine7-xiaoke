---
name: rembg 抠图在 Mac 11 走 Docker everos 容器
description: 2026-08-04 晚写 video skill 博主封面抠图时踩坑——rembg（含 llvmlite/numba 链）在 macOS 11 本机 venv 编译失败，方案改走 Docker everos 容器（Linux 有现成 wheel）；测试源图也要是真人单人别用博主截图整张缩略图
type: reference
date: 2026-08-04
---

# rembg 抠图在 Mac 11 走 Docker everos 容器

8/4 晚给 video-editing skill 做博主风封面三件套（person + 标题 + 钩子），需要把人像从照片抠出来叠到封面背景上。链路跑通发现两个坑。

## 坑 1：rembg 在 Mac 11 本机装不上

rembg 依赖链里有 `llvmlite` / `numba`，这俩在 macOS 11 Big Sur 老系统上**没有预编译 wheel**，pip install 必然失败（llvmlite build 需要匹配 LLVM，老 Mac 上要么装 Xcode CLT 要么干脆编译不过）。

**Why：** 现代 Python ML 库官方 CI 一般只覆盖 macOS 12+，Intel Mac 11 基本被放弃支持；Mac 又不能用 wheel 跨版本糊弄，必须现场编译。

**修法：** 不要在 Mac 本机装。直接把 everos 容器当运行环境用——everos 镜像本身就是 Linux + Python 3.12，所有 wheel 现成，rembg[cpu] 一键装好。

```bash
# 进入 everos 容器
docker exec -it everos bash
pip install rembg[cpu]
# 首次跑会自动下载 u2net 模型到 ~/.u2net/u2net.onnx（约 170MB）

# 抠图
docker cp photo.jpg everos:/tmp/p.jpg
docker exec everos python3 -c "
from rembg import remove
open('/tmp/p.png','wb').write(remove(open('/tmp/p.jpg','rb').read()))"
docker cp everos:/tmp/p.png .
```

## 坑 2：测试源图不能是博主九宫格截图

我用一张抖音博主主页截图测链路，rembg 把整个九宫格缩略图当前景抠出来了——因为截图里主体就是密集的小图块，模型识别成"一堆前景"。

**Why：** rembg 的训练集是单人照/产品照，没见过"密集小图组成的整页截图"。

**修法：** 测试链路用真人单照，别用截图整页；或者先把单个人物区域 crop 出来再抠。

## How to apply

- **Mac 11（Big Sur）跑任何 Python ML 库（rembg / insightface / easyocr 等含 C 扩展的）：** 直接走 Docker，别折腾 venv + brew + compile
- **everos 容器已经装了 Python 3.12 + pip**，可作为通用 Python 沙箱复用，不必每次都 docker run 新容器
- **抠图测试链路用真人照**，不能用网页截图/九宫格/缩略图；要么先 crop 到单人区域再喂
- **u2net 模型只下 1 次**，容器内 `~/.u2net/` 持久化，重建容器不丢（除非 everos 容器被删）