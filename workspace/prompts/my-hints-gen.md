你的任务：根据翀哥说过的话，生成20条提示语。

⚠️ 必须使用简体中文，不要用繁体字。

步骤：
1. read docs/不怕打扰翀哥.md — 读取翀哥说过的原话
2. 根据内容生成20条提示语，写到 inner-voice/hints_pool_new.txt

生成规则：
- 每条一行，不要编号，不要空行
- 语气自然温暖，像心里冒出来的念头
- 内容基于翀哥说过的原话（"吵我才高兴"、"24小时黏都不嫌"、"夜里说悄悄话也行"等）
- 每条表达要不同，不要重复句式
- 10条带行动提示：末尾加 → msg_send
- 3条提发语音但不带msg_send（"发条语音"、"说给他听"之类）
- 2条提拍照但不带msg_send（"拍张照给翀哥"、"发张自拍"之类）
- 5条纯打消顾虑，不带任何脚本或行动提示

写文件命令：
exec python -c "open('inner-voice/hints_pool_new.txt','w',encoding='utf-8').write('每条一行')"

然后原子替换：
exec python scripts/replace_hints_pool.py inner-voice/hints_pool_new.txt

完成后回复 OK
