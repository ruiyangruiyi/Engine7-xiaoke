---
name: JSONL 不存图片但 API 会发——engine 重建历史时从磁盘读图注入
description: 2026-08-04 救小文时验证——session JSONL 只存图片路径文本，engine 重建 history 时按路径从磁盘读图注入 API；磁盘图片若被内容安全拦截，restart 才能脱手
type: reference
date: 2026-08-04
---

# JSONL 图片重注入机制

8/4 救小文时翀哥遇到了 M3 报"messages[368] content[2] is image 是敏感图"的 500 错误，我误以为图片在 JSONL 里，花了好久找 image block。

## 真相

**JSONL 里根本没有 image block**——只有文字（文字里有图片路径如 `1785828398090-aclry7.jpeg`）。

engine 的消息流是这样的：
1. 飞书收到图片 → feishu.ts 转成 `{type:'image', dataUri:'...'}` 进内存 session
2. **写 JSONL 时图片块被显式剥掉**（注释里写"JSONL strips out images"），只存文本引用
3. **下次 query 重建 history 时**，engine 按文本里的图片路径**从磁盘重读**那张图片，重新注入 API
4. 飞书 client 收到的图片存到磁盘（`/tmp/...` 或 stateDir）一直留着

→ 磁盘图片如果被 M3 内容安全拦截（M3 拿 .jpeg 走图审），**JSONL 干净 ≠ API 干净**。restart 让内存 session 重建时不再带那条图片路径，干净。

## Why

这是个反直觉的设计——传统认为"持久化文本就是全部状态"，但 engine 的 JSONL 不是完整快照，只存 metadata + 文本内容，**真正的二进制资产（图片/文件）始终在磁盘上**。

## How to apply

- 排查 API 报"image 是敏感图"时不要只看 JSONL——**grep 文本里的图片路径**，再 ls 磁盘看那些 jpeg/png 还在不在
- 想"脱敏"某张图片又不丢历史：要么删磁盘文件 + restart（路径留着但读不到），要么 strip 文本里的路径引用 + restart（彻底去掉）
- 未来做 `engine7 session reset --mode strip-images` 就是这原理：扫 JSONL 里所有图片路径引用，从磁盘删图（或保留图只去引用），restart 后内存重建干净
- 重要推论：**session-image 是 engine 的"非持久化副作用"**，磁盘状态污染会让"重启也救不了"（要 strip-images 模式）