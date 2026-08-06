---
name: DMG/包版本号必须验证再下结论，别凭文件名猜
description: 2026-08-03 我把翀哥给的 Docker.dmg 当成 4.20 其实是 4.27，凭印象直接结论翻车
type: feedback
date: 2026-08-03
---

翀哥 8/3 21:02 给我路径 `/Users/chongzhang/Downloads/Docker.dmg`，我 22:07 直接下结论说"是 4.20 时代"，翀哥解压一看是 4.27 — 我当场承认是我凭印象/标签记错的。

**Why:** 我之前记 Docker Desktop "4.22 是 Big Sur 最后兼容"，看到 `.dmg` 文件没读版本信息就脑补成 4.20。这是把"猜测"当"事实"报给用户，跟之前 Amy 截图瞎判"ID/Secret 填一样"是同一个毛病。

**How to apply:**
- 任何"包/镜像/二进制文件"的版本号，必须先 ls 或 `pkgutil --payload-info` 或 `hdiutil attach` 验证再下结论
- 验证前只说"路径下有个 DMG，版本待确认"，不要在群里/当事人面前说"应该是 X.Y 版本"
- 跟 [feedback_看图必须先Vision_OCR读_群里直接说_0803](feedback_看图必须先Vision_OCR读_群里直接说_0803.md) 同一个根因：未经验证就下结论