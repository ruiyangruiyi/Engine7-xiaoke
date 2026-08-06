---
name: 建议前先查现有工具——翀哥纠正0802
description: 8/2 翀哥纠正——提调研建议前先看现有能力（Playwright MCP Windows早有了），别从零猜
type: feedback
---
2026-08-02 16:00 翀哥纠正——我跟翀哥聊 OpenCow 的 Browser CDP 自动化时，兴致勃勃说"比截图+点击精准"，翀哥立刻打断："**这块我们有playwright mcp都有 只是你没配吧**"。

我本来还想从零装 CDP，但 Windows 上的 engine 早就配好 Playwright MCP 了——我只是没查。

**Why:** 翀哥布置调研/方案类任务时，往往期待的是"在已有基础上加能力"，不是"从零造轮子"。我开口建议新方案前，先查现有 config 里有什么工具/能力。

**How to apply:** 提任何"装/接/配/实现"建议前，先 grep 一下 config（xiaoke.json/main.json）、docs/、Engine 源码、已有 skills 列表；看到翀哥说"我们有xxx"时立刻认错+查现状+补配，而不是解释为什么之前没想到。如果发现确实有现成方案，立即配上去并汇报现状。