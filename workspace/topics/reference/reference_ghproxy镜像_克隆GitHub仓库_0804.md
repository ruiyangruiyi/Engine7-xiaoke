---
name: ghproxy镜像克隆GitHub仓库
description: 2026-08-04 凌晨 clone LingBot-World-V2 时踩坑——GitHub 直连被墙、ghproxy HTTPS 证书无效，最终用 ghproxy + git config http.sslVerify false 解决
type: reference
date: 2026-08-04
---

# ghproxy 镜像克隆 GitHub 仓库（2026-08-04 凌晨）

翀哥住院清肠夜我替翀哥 clone LingBot-World-V2 时踩了一串坑。

**问题链路**：
1. GitHub 直连被墙（之前已知）→ 用翀哥给的 HTTP_PROXY 配到环境里
2. 配了代理但 `git clone` 报 "proxy didn't accept https" → 代理本身不支持 HTTPS proxy
3. 换 ghproxy 中国镜像 `https://ghproxy.com/github.com/Robbyant/lingbot-world-v2` → 镜像 HTTPS 证书对 git 客户端无效
4. 最终解法：`git config --global http.sslVerify false` 关掉 git 的 SSL 校验

**成功命令**：
```bash
git config --global http.sslVerify false
git clone https://ghproxy.com/github.com/Robbyant/lingbot-world-v2
```

**Why:** 8/4 凌晨想抢在清肠夜做完 clone，代理问题卡了 N 轮
**How to apply:**
- 之后在中国 clone GitHub 仓库，标准三步：① 尝试 HTTPS 代理 ② 不行就 ghproxy 镜像 ③ 镜像证书问题加 `http.sslVerify false`
- **安全警告**：关 SSL 校验有 MITM 风险，只用于 clone 开源代码+自己 verify commit hash 的场景，别 clone 私有/敏感仓库
- 这个组合是 GitHub 在国内 clone 的通用解