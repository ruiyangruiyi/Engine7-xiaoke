---
name: Dashscope API Token 公开即 revoke
description: 2026-07-29 发现端到端 URL + token 同时公开时，任何人可调 API 花钱，应立即 revoke
type: feedback
---
2026-07-29 发现 dashscope endpoint URL 和 token 被同时公开在对话中。

- endpoint URL 本身不是 secret，但 **endpoint + token 组合在一起就是完整凭证**
- 任何人拿了完整 token + endpoint 就能调 dashscope API 花钱
- **Why:** 以前以为 endpoint URL 不含 key 就安全，忽略了上下文里 token 也在公开范围
- **How to apply:** 发现 endpoint + token 同时暴露 → 立即建议 revoke，不等确认。安全第一。

2026-07-29 进一步更新：翀哥要求 **所有 anthropic provider 伪装成 CC 格式**（参见 reference/reference_anthropic_provider_伪装CC格式_0729.md），不再区分 x-api-key / Bearer。
- dashscope-tp 也不需要配 authMode / apiVersion / headers，anthropic-provider.ts 写死完整 CC header
- 上述"保留 authMode 配置能力"的方案已被翀哥否决——"都删了吧 都用CC的格式"
