---
name: macOS echo -n 不是禁止换行而是当文字输出
description: 2026-08-02 晚微信操作脚本踩坑——macOS /bin/sh 的 echo 把 -n 当普通文字输出，粘贴板里有 -n 残留导致搜索失败，必须改用 printf '%s'
type: feedback
---
2026-08-02 晚实操微信 Mac 客户端时踩到：Vision OCR 读到联系人项是 `Q -n 张翀`，` -n ` 不是 OCR 错误也不是微信 UI 标注——是我用 `echo -n "张翀"` 输出到粘贴板时，macOS `/bin/sh` 的 `echo` **把 `-n` 当普通文字输出了**，粘贴板里实际是 `-n张翀`。

**根因**：
- Linux 的 bash 内建 `echo` 默认支持 `-n`（= 不输出尾换行）
- macOS 的 `/bin/sh`（dash 系）`echo` **也支持 `-n`**，但当传给外部命令（`pbcopy` / 管道）时参数解析不一致，行为不可靠
- 安全做法：**永远用 `printf '%s' "内容"` 而不是 `echo -n`**

**Why:** macOS shell 跟 Linux 有微妙差异，`echo -n` 在脚本里跨平台不可靠。以后任何"输出一段不带尾换行的内容到管道/文件/粘贴板"的场景都要警惕。

**How to apply:**
- 写 shell 脚本时 **不用 `echo -n`，改用 `printf '%s' "..."`**
- pbcopy 输出：`printf '%s' "内容" | pbcopy`
- 重定向到文件不带换行：`printf '%s' "内容" > file`
- 如果非要用 echo，至少加 `-e` 和显式 `\c` 兜底（`echo -e "内容\c"`）——但不如 printf 干净