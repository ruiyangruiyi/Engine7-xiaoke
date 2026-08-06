# Carpo Linux .so 编译

**日期：** 2026-07-05

## 背景

Carpo 原始 SDK 只有 Android (.so for ARM) 和 Windows (DLL for x64) 的编译配置。7/5 在 AutoDL (x86_64 Linux) 上编译 `libcarpo.so`，用于 Python ctypes 直接调用。

## 环境

| 项目 | 值 |
|------|-----|
| 机器 | AutoDL 4090 (Ubuntu, x86_64) |
| SSH | `connect.bjb1.seetacloud.com:40458` root/NIgDNE+SPYSM |
| 编译器 | g++ / gcc |
| Python | `/root/autodl-tmp/envs/flashhead/bin/python3` (Python 3.10) |
| 构建目录 | `/root/carpo_build/` |
| 部署目录 | `/root/carpo_sdk/libcarpo.so` |

## 编译方案：按 Android.mk 提取文件列表

**不是手写文件列表，是从 Android.mk 自动提取的。** 原始 `D:/work/code/LovePea/Carpo/Carpo/android/Android.mk` 包含完整的源文件列表（263 个文件）。

脚本 `build_android_v2.sh` 把 Android.mk 里的文件列表提取出来，逐个编译为 .o，最后 link 成 .so。

### 编译参数

```bash
CXXFLAGS="-fPIC -O2 -std=c++11 -DNDEBUG -D_LINUX -DWEBRTC_POSIX \
  -DWEBRTC_CLOCK_TYPE_REALTIME -DWEBRTC_CODEC_OPUS -DWEBRTC_LINUX \
  -D__STDC_CONSTANT_MACROS -D__STDC_FORMAT_MACROS \
  -DWEBRTC_AEC_DEBUG_DUMP=0 -DWEBRTC_NS_FIXED \
  -fexceptions -fpermissive \
  -include condition_variable -include atomic -include algorithm \
  -include functional -include cstddef -include cstring -include memory"

INCLUDES="-I. -I3rdparty/include -I3rdparty/include/opusAndroid \
  -I3rdparty/include/c-ares -I/usr/include/opus \
  -Isrc -IRtpRtcp -IToolkit -Iexport -INetwork -IAudioCodec \
  -Icjson -Iwebrtc -Icarpo_capi"

LIBS="-L/usr/lib/x86_64-linux-gnu -lopus -lcurl -lcares -lpthread -lstdc++"
```

关键 define：
- `-DWEBRTC_POSIX` — POSIX 平台（必须有，否则大量编译失败）
- `-DWEBRTC_LINUX` — Linux 平台
- `-DWEBRTC_CODEC_OPUS` — Opus 编解码
- `-D_LINUX` — Carpo 自己的 Linux 标记

## 编译步骤

```bash
# 1. SSH 进 AutoDL
ssh root@connect.bjb1.seetacloud.com -p 40458

# 2. 进入构建目录
cd /root/carpo_build

# 3. 全量编译 + 链接
bash build_android_v2.sh
# 输出：263 文件编译，~272 .o（部分文件有 .c 和 .cc），2MB libcarpo.so

# 4. 部署
cp libcarpo.so /root/carpo_sdk/libcarpo.so
```

## 增量编译（改单个文件后）

```bash
# 只编译改了的文件
cd /root/carpo_build
g++ -fPIC -O2 -std=c++11 -D_LINUX -DWEBRTC_POSIX -DWEBRTC_LINUX -DWEBRTC_CODEC_OPUS \
  -fpermissive -include condition_variable -include atomic -include algorithm \
  -include functional -include cstddef -include cstring -include memory \
  -I. -I/usr/include/opus -I3rdparty/include -Isrc -IRtpRtcp -IToolkit -Iexport \
  -INetwork -IAudioCodec -Icjson -Iwebrtc -Icarpo_capi \
  -c RtpRtcp/PacedSender.cpp -o build/RtpRtcp_PacedSender.cpp.o

# 重新链接
OBJS=$(find build -name "*.o" | sort)
g++ -shared -Wl,--allow-multiple-definition -o libcarpo.so $OBJS \
  -L/usr/lib/x86_64-linux-gnu -lopus -lcurl -lcares -lpthread -lstdc++ \
  -L/root/autodl-tmp/envs/flashhead/lib -lpython3.10

# 部署
cp libcarpo.so /root/carpo_sdk/libcarpo.so
```

## 遇到的问题与解决

### 1. 252 个 undefined symbol

**根因：** 缺 `-DWEBRTC_POSIX`，导致大量 WebRTC 代码走了错误的条件编译分支。

**解决：** 加 `-DWEBRTC_POSIX`。

### 2. WebRtcSpl 函数指针 null (crash)

**根因：** `webrtc/common_audio/signal_processing/spl_init.c` 在 x86 平台上没初始化 9 个函数指针（原代码只初始化 ARM/NEON 版本）。

**解决：** 补 `stub_spl.c`，手动初始化 9 个函数指针指向 C 实现：

```c
WebRtcSpl_MaxAbsValueW16 = WebRtcSpl_MaxAbsValueW16C;
WebRtcSpl_MaxAbsValueW32 = WebRtcSpl_MaxAbsValueW32C;
WebRtcSpl_MaxValueW16 = WebRtcSpl_MaxValueW16C;
WebRtcSpl_MaxValueW32 = WebRtcSpl_MaxValueW32C;
WebRtcSpl_MinValueW16 = WebRtcSpl_MinValueW16C;
WebRtcSpl_MinValueW32 = WebRtcSpl_MinValueW32C;
WebRtcSpl_MaxAbsDiffW16 = WebRtcSpl_MaxAbsDiffW16C;
WebRtcSpl_MaxAbsDiffW32 = WebRtcSpl_MaxAbsDiffW32C;
WebRtcSpl_VectorMaxMinW16 = WebRtcSpl_VectorMaxMinW16C;
```

### 3. WebRtc_GetCPUInfo 缺失

**根因：** `cpu_info.cc` 在 x86 平台调 `WebRtc_GetCPUInfo`，但 x86 实现没编译进去。

**解决：** 补 `cpu_info_stub.c`，用 `__builtin_cpu_supports` 替代 cpuid 检测。

### 4. auto_correlation.c 缺失

**解决：** 从 WebRTC 源码补 `webrtc/common_audio/signal_processing/auto_correlation.c`。

### 5. SSE2 文件缺失

**解决：** 补 `fir_filter_sse.c` / `aec_rdft_sse2.c` / `aec_core_sse2.c`。

### 6. Python GIL crash

**根因：** Carpo callback 在 C 线程调 Python 函数，没持有 GIL。

**解决：** `carpo_capi.cpp` 里用 `PyGILState_Ensure()/PyGILState_Release(state)` 包裹 callback。

## 编译验证

```bash
# 加载测试
LD_LIBRARY_PATH=/root/carpo_sdk:$LD_LIBRARY_PATH \
  /root/autodl-tmp/envs/flashhead/bin/python3 -c \
  "import ctypes; ctypes.CDLL('/root/carpo_sdk/libcarpo.so'); print('LOADED OK')"

# undefined symbol 检查（应该为 0 或只有 std/pthread/GLIBC）
nm -D /root/carpo_sdk/libcarpo.so 2>/dev/null | grep " U " | \
  grep -iv "std\|pthread\|GLIBC\|GLIBCXX\|CXXABI\|GCC_" | wc -l
```

## 产出

```
/root/carpo_sdk/libcarpo.so  (~2MB)
```

## 关键文件

| 文件 | 说明 |
|------|------|
| `D:/work/code/LovePea/Carpo/carpo_capi/build_android_v2.sh` | 主编译脚本（272 文件列表） |
| `/root/carpo_build/stub_spl.c` | WebRtcSpl x86 函数指针初始化 |
| `/root/carpo_build/cpu_info_stub.c` | CPU info x86 stub |
| `D:/work/code/LovePea/Carpo/carpo_capi/carpo_capi.cpp` | C Wrapper（含 GIL 处理） |

---

# Windows Carpo.dll 编译

**日期：** 2026-07-05（首次），2026-07-06（加 log 重编）

## 环境

| 项目 | 值 |
|------|-----|
| MSBuild | VS2022 BuildTools v143 |
| 路径 | `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\amd64\MSBuild.exe` |
| 工程 | `D:\work\code\LovePea\platform\Windows\LovePeaSDK\LovePeaSDK.sln` |
| 项目 | `Carpo\Carpo.vcxproj` |
| 配置 | Release / x64 |
| 产出 | `platform\Windows\LovePeaSDK\x64\Release\Carpo.dll` |
| 运行时 | 同目录（DLL + 所有依赖 DLL 都在这） |

## 编译命令

```bash
# 找 MSBuild（vswhere 自动定位）
"/c/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe" \
  -latest -products '*' -requires Microsoft.Component.MSBuild \
  -property installationPath

# 编译 Carpo.dll
MSBUILD="C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/MSBuild/Current/Bin/amd64/MSBuild.exe"
"$MSBUILD" "D:/work/code/LovePea/platform/Windows/LovePeaSDK/Carpo/Carpo.vcxproj" \
  -p:Configuration=Release -p:Platform=x64 -m -verbosity:minimal

# 覆盖运行时 DLL（需要先停掉占用 DLL 的 Python 进程）
cp "D:/work/code/LovePea/platform/Windows/LovePeaSDK/Carpo/x64/Release/Carpo.dll" \
   "D:/work/code/LovePea/platform/Windows/LovePeaSDK/x64/Release/Carpo.dll"
```

## 注意事项

- **VS2017 只有 v141 工具集**，Carpo.vcxproj 要求 v143（VS2022），必须用 VS2022 BuildTools
- **DLL 被占用时无法覆盖**（Device or resource busy）——先 Ctrl+C 停掉 pull_play_auto.py
- LNK4099 PDB 警告不影响功能

---

# 2026-07-06 排查记录

## 环境（089 机器，换机后从零搭建）

| 项目 | 值 |
|------|-----|
| 机器 | AutoDL 089 (Ubuntu, x86_64) |
| SSH | `connect.bjb1.seetacloud.com:37725` root/m13T28fZq/XI |
| 公网 IP | 106.39.200.204 |
| Python | `/usr/bin/python3` (3.10)，**不是** miniconda3 的 3.12 |

### 换机后必须做的事
1. `apt install libopus-dev libcurl4-openssl-dev libc-ares-dev`
2. 上传 Carpo 源码 tar（不含 3rdparty，48MB）
3. 上传 `build_android_v2.sh`（已补全 272 文件）
4. 创建 `stub_spl.c` + `cpu_info_stub.c`
5. `bash build_android_v2.sh` 全量编译
6. `pip install scipy dashscope av`（装到系统 python3，不是 miniconda）

### build_android_v2.sh 7/6 补全的文件（+9）
- `carpo_capi/carpo_capi.cpp` — C Wrapper
- `stub_spl.c` — WebRtcSpl x86 初始化
- `cpu_info_stub.c` — WebRtc_GetCPUInfo
- `AudioCodec/cp_pcm_split_fixed_slice.c`
- `AudioCodec/cp_av_frame.c`
- `webrtc/.../auto_correlation.c`
- `webrtc/.../fir_filter_sse.cc`
- `webrtc/.../aec_core_sse2.cc`
- `webrtc/.../aec_rdft_sse2.cc`

### 新增编译参数
- `-DWEBRTC_ARCH_X86_FAMILY` — x86 SSE2 支持（没有它 WebRtc_GetCPUInfo 不被调用，运行时 undefined symbol）
- `-msse2` — SSE2 指令集
- `-L/root/autodl-tmp/envs/flashhead/lib -lpython3.10` — 链接 Python（GIL 支持）

## 问题排查

### 1. Windows pull 端 0 个 UDP 包到 server

**现象：** pull_play_auto.py 跑了，但 server tcpdump 抓不到 Windows IP 的任何 UDP 包。同机器跑 `test_udp.py`（纯 Python socket）能到。

**根因：** `socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)` 返回 -1。Windows DLL 内部没调 `WSAStartup()` 初始化 Winsock。

**调试关键：** 先调 `LogOpen(None, 0x1111)` 开启 MeetingLog 日志（默认 g_logLevel=0 全部跳过），才能看到 `UdpPeer createPeer socket fd = -1`。

**解决：** pull_play_auto.py 加 WSAStartup：
```python
ws2 = ctypes.windll.ws2_32
class WSAData(ctypes.Structure):
    _fields_ = [...]
wsa = WSAData()
ws2.WSAStartup(0x0202, ctypes.byref(wsa))
```

### 2. Server crash（udp_server.cc:329）

**现象：** 重建 Docker 容器后，server 一收到 askPlay 就 crash（exit 139）。

**根因：** `udp_server.cc:310-332` 主循环检查 server 是否注册到 master_server。重建容器后 `--master_server=127.0.0.1:50051` 的注册失败（master 没跑），main loop 检测到后 `return 0` 直接退出。

**日志特征：**
```
W udp_server.cc:328] please registe the server!!!
terminate called without an active exception
```

**修复方向：** 把 `return 0` 改成 `continue`（重试注册），或者确保 master_server 在跑。

### 3. Python 路径问题

**现象：** `pip install` 装了包，但 `python3` 跑脚本报 `ModuleNotFoundError`。

**根因：** AutoDL 默认 `python3` 是 miniconda3 的 Python 3.12，跟 `pip install` 装到的系统 Python 3.10 不同。miniconda3 的 libstdc++ 版本太旧（GLIBCXX_3.4.30 not found）。

**解决：** 用 `/usr/bin/python3`（系统 Python 3.10）跑脚本。

### 4. clash 拦截 UDP（排除）

重启 Windows 后确认 clash 不是根因——`test_udp.py` 能发 UDP 到 server。问题确实在 Carpo DLL 内部。

## Server 环境

| 项目 | 值 |
|------|-----|
| Server | 北京腾讯云 `192.144.156.158` |
| SSH | ubuntu/Lh123456! |
| Docker | `carpo-server:latest`，端口 23800/udp |
| Binary | bazel-bin/server/udp_server（在 Docker image 内） |
| Server 源码 | `D:/work/code/carpo/`（本地），bazel 构建 |
| 启动命令 | `udp_server --logtostderr=1 --redis_ip=127.0.0.1 --redis_port=36379 --master_server=127.0.0.1:50051` |

### Server 调试环境搭建（7/6）
- server 源码已传到北京 server `/root/carpo_src/`（0.1MB tar，只有 server+modules）
- Docker 容器已加 `-v /root/carpo_src:/root/carpo_src` 映射
- 但 Docker 里 bazel 编译环境还需要验证（源码在 host，bazel cache 在 container）

### askPlay 回 ACK 的条件（server 源码分析）

`command_interpreter.cc:146` CMD_PULL 分支：
1. `startPull(wish_ssrc, wish_ip)` 返回 true 才回 ACK
2. `wish_ip == 0` → 返回 false，不回 ACK
3. `wish_ip` 是自己 → 返回 false
4. 本地有流 或 成功创建穿透 → 返回 true，回 ACK

**pull 端 askPlay 包的 ipWatch 字段** 来自 `RTPTransport::remote_ip_`（`RTPTransport.cpp:1009`）。如果没设 remote_ip，ipWatch=0，server 不回 ACK。

pull 端设 remote_ip：
```python
puller.set_server('192.144.156.158', 23800, remote_ip='106.39.200.204')
```
