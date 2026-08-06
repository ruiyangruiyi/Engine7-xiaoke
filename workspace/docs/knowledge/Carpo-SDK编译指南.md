# Carpo SDK 编译指南

**日期**：2026-07-02
**环境**：Windows 10 x64 + VS2022 BuildTools (v143)

## 背景

Carpo 是新浪的视频实时通信 SDK（类似 WebRTC 的 RTP/RTCP 子集），包含推流（PushSender）和拉流（PullReceiver）两端。原项目用 VS2010 (v100) 编译，需迁移到 VS2022。

## 源码位置

```
D:/work/code/LovePea/
├── Carpo/Carpo/              ← SDK 源码（C++）
│   ├── export/               ← 公共头文件（PushSender.h, PullReceiver.h, factory.h）
│   ├── src/                  ← 核心实现
│   ├── RtpRtcp/              ← RTP/RTCP 协议
│   ├── Network/              ← 网络层（TcpPeer, UdpPeer）
│   ├── AudioCodec/           ← Opus 编解码
│   ├── webrtc/               ← WebRTC 模块（134 个源文件）
│   ├── 3rdparty/             ← 第三方依赖（protobuf, opus, silv
    └── carpo_capi/           ← C ABI Wrapper（我们加的）
│       ├── carpo_capi.h
│       ├── carpo_capi.cpp
│       └── python/
└── platform/Windows/LovePeaSDK/
    ├── Carpo/Carpo.vcxproj   ← 主工程文件
    ├── MeetingLog/            ← 日志库（依赖）
    └── include/               ← 公共头文件（RDMutex.h 等）
```

## 编译顺序

```
LiveBase.lib → MeetingLog.lib/DLL → Carpo.dll
```

三个工程独立编译，Carpo 依赖前两者。

## 修改清单（6 个文件）

### 1. Carpo.vcxproj — PlatformToolset 升级
```xml
<!-- 旧 -->
<PlatformToolset>v100</PlatformToolset>
<!-- 新 -->
<PlatformToolset>v143</PlatformToolset>
```
同时 Release|x64 的 AdditionalIncludeDirectories 加了 `carpo_capi` 目录。

### 2. carpo_log.h — 补 CP_INFO_LOG 宏
Windows 分支缺少 `CP_INFO_LOG` 宏定义，Linux 分支有。直接复制 Linux 版到 Windows 分支。

### 3. AudioMixer.h — 补 #include <chrono>
VS2022 更严格，`std::chrono` 需要显式 include。

### 4. MeetingLog.cpp — 去掉 RDMediaCommon.h
`RDMediaCommon.h` 依赖 `atlbase.h`（ATL），VS2022 BuildTools 不含 ATL。MeetingLog 不需要 ATL，直接删除 include。

### 5. RDMediaCommon.h — 注释掉 ATL
```cpp
// #include <atlbase.h>
// #include <atlwin.h>
```

### 6. factory.cpp — stub AudioSignalProcessingInner
`AudioSignalProcessingInner` 依赖 `webrtc::AudioProcessing`（AEC/AGC/NS），推流端不需要。返回 null stub。
```cpp
// 原来调用 Factory::createAudioSignalProcessing()
// 改为直接 return nullptr
```

### 补充：vcxproj 添加缺失源文件
- `Network/HttpPeer.cpp`（HTTP 上报）
- `Toolkit/CarpoEsLog.cpp`（统计上报）
- `carpo_capi/carpo_capi.cpp`（C Wrapper）

## 编译命令

```bash
MSBuild.exe Carpo.vcxproj /p:Configuration=Release /p:Platform=x64 /t:Rebuild /v:minimal
```

## DLL 依赖

Carpo.dll 运行时依赖以下 DLL：

| DLL | 来源 | 说明 |
|-----|------|------|
| MeetingLog.dll | 本项目编译 | 日志库 |
| pthreadVC2.dll | 预编译 | POSIX 线程，依赖 **MSVCR110.dll**（VS2012） |
| MSVCP140.dll | VC++ Redist 2015-2022 | C++ 标准库 |
| VCRUNTIME140.dll | VC++ Redist 2015-2022 | C 运行时 |

### 需要安装的 VC++ Redistributable

系统干净安装时需要装以下三个（各版本 Side-by-Side，不冲突）：

1. **VC++ 2010 SP1 Redist x64** — MSVCR100.dll（MeetingLog 依赖）
2. **VC++ 2012 Update 4 Redist x64** — MSVCR110.dll（pthreadVC2 依赖）
3. **VC++ 2015-2022 Redist x64** — MSVCP140/VCRUNTIME140（Carpo 自身）

下载链接：
- 2010: https://www.microsoft.com/en-us/download/details.aspx?id=26999
- 2012: https://www.microsoft.com/en-us/download/details.aspx?id=30679
- 2022: https://aka.ms/vs/17/release/vc_redist.x64.exe

## 输出

```
D:/work/code/LovePea/platform/Windows/LovePeaSDK/Carpo/x64/Release/Carpo.dll
大小：~1.2MB
```

## 编译后的 WebRTC 模块覆盖

134 个 WebRTC 源文件编入 Carpo.dll：

| 模块 | 功能 |
|------|------|
| rtp_rtcp | RTP 打包/解包，H.264/VP8/VP9 格式化 |
| remote_bitrate_estimator | 带宽估计（AIMD） |
| video_coding | Jitter buffer，帧缓冲 |
| audio_coding | Opus 编解码 + NetEq 抖动缓冲 |
| common_audio | VAD，信号处理，FFT |
| common_video/h264 | SPS/PPS 解析，NAL 分包 |
| system_wrappers | 时钟，线程，锁，日志 |
| base | Buffer，线程检查，时间工具 |

**未编入**：AudioSignalProcessingInner（AEC/AGC/NS），双向语音聊天时需要加回来。
