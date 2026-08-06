---
name: wx_query 是 Windows 专用，Mac 端不可用
description: 2026-08-02 验证——wx_query 路径写死 Windows（wxdump.exe + C:/Users/24045/...），Mac 微信数据库格式/路径/加密方式不同，整个搬不过来
type: reference
---
8/2 晚翀哥问 Mac 端能不能用 wx_query 读微信消息，验证：**不行**。

**根因（三层都不可移植）**：
1. **路径写死**：`C:/Users/24045/Documents/WeChat Files/` —— Mac 是 `~/Library/Containers/com.tencent.xinWeChat/...`
2. **依赖 `wxdump.exe`**（从微信进程内存提取 SQLCipher 密钥）—— Windows-only 工具，Mac 微信进程不是 `Weixin.exe`，加密密钥提取方案不一样
3. **Mac 微信数据库格式不同**：Mac 微信是独立的 `xwechat` 客户端，数据库结构、加密方式、路径都跟 Windows 不一样

**Mac 端已有替代方案**：
- **读消息**：Vision OCR 截图 + OCR 文字识别（已实测可读聊天列表）
- **发消息**：AppleScript + pbcopy + Vision OCR（已实测成功发到文件传输助手）
- **Mac 微信数据库解密**：暂无现成方案，需要调研（PyWxDump 不支持 Mac）

**Why:** 之前所有微信 reader 设计都基于 Windows。翀哥老家用 Mac（Big Sur 11），不能再依赖 wx_query。

**How to apply:**
- **翀哥在 Mac 上**：微信消息读取走 Vision OCR 截图方案，不指望 wx_query
- **翀哥在 Windows 上**（回北京后）：wx_query 继续走 PyWxDump + 解密缓存
- 如果以后要做 Mac 微信数据库解密，需要调研 macOS 版的内存密钥提取工具（可能需要 Frida hook WeChat 进程），不是 wx_query 直接搬