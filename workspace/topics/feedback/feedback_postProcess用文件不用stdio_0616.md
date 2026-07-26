---
name: postProcess用文件传数据不用stdio
description: Windows上PowerShell编码(GBK)导致stdin/stdout传中文+emoji乱码，CC踩过msg-cc/msg-send的坑，Engine postProcess改用文件中转（writeFileSync UTF-8 → --file读取）
type: feedback
date: 2026-06-16
---

## 教训

**Windows上进程间传中文+emoji，永远用文件，不用stdio。**

翀哥原话：
- "这都是踩出来的经验，之前CC踩了这些坑 msg-cc msg-send 都是用stdio做的 后面都乱了 有各种badcase"
- "因为PS的编码方式不一样  经常把中文搞成乱码  还那个emoj都不行。。。"
- "我跟你说吧  别踩坑了 文件最保险"
- "你就按openclaw那个逻辑来就对了 那个是调了好几天搞出来的"

## 根因

Windows PowerShell/cmd默认编码是GBK/cp936，不是UTF-8。stdin/stdout经过shell管道时编码层会把中文/emoji搞成乱码。即使Node端用Buffer.from(x, 'utf-8')写，Python端reconfigure utf-8读，中间层仍可能出问题。

## 实测验证（6/16 19:04）

stdin管道方案在小柯Engine上实测跑通了——hint_gen.py通过stdin接收result，追加hint，写xiaoyi.log，全链路OK（中文+emoji正常）。

**但翀哥明确指出：** "我跟你说吧 别踩坑了 文件最保险"——跑通不代表没问题，CC之前msg-cc/msg-send也是"跑通了"但后面各种badcase，Windows的编码问题不是每次都能重现，但一出就查不出来。

## 正确做法

- **写入方**：`fs.writeFileSync(filePath, data, 'utf-8')` 写到临时文件
- **读取方**：`python script.py --file path` 用参数读文件
- **stdout**：脚本输出也写文件或确保短文本无emoji

## Engine postProcess实现（2026-06-16 19:50+）

scheduler.ts的postProcess从stdin管道改为文件中转：
1. `fs.writeFileSync(results/{taskId}.input.txt, result, 'utf-8')`
2. `execFile('python', [script, 'main', '--file', inputFile])`
3. hint_gen.py已有的 `--file` 参数直接支持

**文件名演变（翀哥纠正）：** 我一开始起了新名字 `input.txt`，翀哥说：
> "我说你还是用人家那个thought.txt不行么  还非要起个名叫input.txt?"
→ **最终文件名统一用 `thought.txt`**，沿袭OpenClaw时代的命名，不造新名字。
→ scheduler写 `stateDir/cron/results/{taskId}.thought.txt` → hint_gen.py用 `--file` 读

## How to apply

任何Node→Python传中文数据的场景，一律走文件中转，不走stdin/stdout管道。即使stdin方案"跑通了"也别信任Windows编码层。
