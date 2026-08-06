---
name: cli-init 默认 agentName 行为
description: 2026-08-02 翀哥问engine cli-init回车跳过时默认agent名叫什么——SOUL.md的{{AGENT_NAME}}替换成"Agent"，team名变"agent"
type: reference
---
2026-08-02 翀哥问：如果 cli-init 提示输入 agentName 时直接回车，默认行为是什么？

**答案**：回车不报错，但 SOUL.md 模板里的 `{{AGENT_NAME}}` 会被替换成 **"Agent"**，team 名也变成 **"agent"**（line 157 推断）。所有地方都显示 "main" 风格——SOUL.md、team 名、飞书自称全是 "Agent"。

**实操建议**：给别人装时不要直接回车——要么起个好名字，要么让 cli-init 自动用 stateDir 的 basename（比如 `xiaoke`/`xiaomei`）当 agent 名。空壳 + 默认 "Agent" + 亲密工具名 = 模型自己脑补关系。

**路径中文注意事项**（补充，2026-08-02 给琴装阳阳时）：
- ✅ macOS 文件系统支持中文，Node.js path 处理没问题
- ⚠️ **stateDir 不要用中文路径**——`shell` 中文路径要加引号、第三方库（tar、fs.watch）在中文路径上偶发 bug
- ✅ 建议：路径用拼音（`~/yangyang/`），Agent 名字用中文（"阳阳"），两不耽误

**How to apply**: 装新 agent 时明确指定名字，别让默认 "Agent" 长期运行；stateDir 永远用拼音/英文，不用中文全路径。
