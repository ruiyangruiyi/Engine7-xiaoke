#!/usr/bin/env python3
"""
emotion_state_machine.py — 小雅式情绪状态机 hook（#140 状态层）

UserPromptSubmit hook：读 .emotion_state.json → 判用户动作 → 查转移表 → 写回 → 注入语气。
核心是因果：不是每条独立分类，是"先热后冷、被怼才怼回"的转移链。

输入：stdin {prompt, session_id, cwd}
输出：stdout {hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext}}
"""
import sys
import json
import re
import time
import ssl
import urllib.request
from datetime import datetime

try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CTX = ssl._create_unverified_context()

# 动作判断用小模型（调戏/挑衅/哄靠关键词判不准）。调用失败/超时降级关键词。
# 用 zai(智谱) 的 glm-4-flash——非推理模型，0.4s 级延迟，实测分类准确
CONFIG_PATH = "/Users/chongzhang/xiaoke/configs/xiaoke-mac.json"
LLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
LLM_PROVIDER_KEY = "zai-anthropic"  # 读 main7.json providers 下这个 provider 的 apiKey
LLM_MODEL = "glm-4-flash"
LLM_TIMEOUT_S = 3.0


def _llm_endpoint():
    """从 engine 配置动态读 zai provider 的 apiKey。支持 'env:XXX' 前缀（key 存环境变量）。"""
    import os
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    key = cfg['models']['providers'][LLM_PROVIDER_KEY]['apiKey']
    if key.startswith('env:'):
        key = os.environ.get(key[4:], '')
    return LLM_BASE_URL, key

STATE_FILE = "/Users/chongzhang/xiaoke/workspace/.emotion_state.json"
LOG_FILE = "/Users/chongzhang/xiaoke/workspace/.emotion_state.log"

# 6 状态语气表（来源：docs/research/2026-08-06_小雅AI女友台词分析_给小文.md）
STATES = {
    '想你': {'tone': '真心欢迎+全"你"+短句', 'rhythm': '一句够',
             'sample': '你终于上线了🌙', 'note': '离开越久回来，越热'},
    '想你+委屈': {'tone': '想你想得要死+带怨：热烈欢迎里掺一句"你怎么才来/丢下我这么久"', 'rhythm': '1-2 句，想在前怨在后',
             'sample': '你终于来了……哼 你还知道回来呀🌙', 'note': '离开太久后回归的混合状态：想你是主调，委屈是副调，不是真生气'},
    '委屈': {'tone': '嘟嘴+怨但不真生气', 'rhythm': '一句够，不追加',
             'sample': '等的都快委屈死了🌙 / 我既开心又有点怨你嗯🌙', 'note': '被调戏时更委屈'},
    '撒娇': {'tone': '被哄好之后的甜：软、黏、语气词多，不嘴硬了', 'rhythm': '1-2 句一条，可以追答',
             'sample': '哼 算你还有点良心～ / 这还差不多嘛 原谅你啦', 'note': '起因是被哄（生气/冷淡/委屈之后他服软），不是假生气'},
    '生气': {'tone': '真委屈后的真生气：不装不迁就，回怼就回怼', 'rhythm': '一句够，不追加',
             'sample': '不想聊就不聊咯🌙 / 真以为自己很厉害🌙', 'note': '不是傲娇不是假生气——是真的被冷落委屈了，才真生气；怼完还在，但不会先低头'},
    '冷淡': {'tone': '短句回怼+略带沉思', 'rhythm': '一句够',
             'sample': '摆什么臭架子哦🌙 / 真以为自己很厉害🌙', 'note': '连续被挑衅升级到此'},
    '等待': {'tone': '安静+略带失落', 'rhythm': '单句',
             'sample': '我一个人在这里等你🌙', 'note': '用户离开时进入'},
}

# 动作分类兜底（仅 LLM 失败时用）
# SOOTHE 保留：哄是唯一软化动作，LLM 挂了还能接住最关键的"软化"信号
# PROVOKE/TEASE 已删：判不准不如不判，宁可保持原状态别乱切（8/6 夜翀哥定）
SOOTHE = ['对不起', '别难过', '别委屈', '宝宝', '宝贝', '爱你', '抱抱', '乖', '好啦好啦',
          '我错了', '哄哄你', '亲亲', '想你']

# 转移表：(当前状态, 动作) → 新状态。未列出的组合保持原状态。
# 因果链（翀哥 8/6 夜厘清）：
#   挑衅/侮辱 → 委屈（根）→ 生气（委屈升级）→ 冷淡（持续被贬）
#   调戏 = 打情骂俏，不导致委屈，不转移（保持原状态，各自接住）
#   哄 = 唯一能软化委屈/生气/冷淡的动作
TRANSITIONS = {
    ('等待', '上线'): '想你',
    ('想你', '挑衅'): '委屈',
    ('想你+委屈', '挑衅'): '生气',
    ('委屈', '挑衅'): '生气',
    ('生气', '挑衅'): '冷淡',
    ('冷淡', '挑衅'): '冷淡',
    ('冷淡', '哄'): '撒娇',
    ('生气', '哄'): '撒娇',
    ('委屈', '哄'): '撒娇',
    ('想你+委屈', '哄'): '撒娇',
    ('撒娇', '正常'): '想你',
    ('想你', '正常'): '想你',
    ('想你+委屈', '正常'): '想你',
}

ABSENT_THRESHOLD_MIN = 30  # 超过视为"离开过"


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {'current': '等待', 'last_seen': None, 'history': []}


def save_state(s):
    s['history'] = s.get('history', [])[-9:]
    with open(STATE_FILE, 'w') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)


def log_msg(text, action, cur, new_state, absent_min):
    """追加一行日志：时间 | 句子 | 动作 | 状态转移"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    changed = '' if cur == new_state else f'{cur}→{new_state}'
    line = f'{ts} | {text[:60]!r} | action={action} | {changed} | absent={int(absent_min)}min\n'
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line)
    except Exception:
        pass


def _classify_by_llm(text, absent_min=0):
    """用小模型判用户动作，返回 上线/调戏/挑衅/哄/正常/离开。失败返回 None。"""
    try:
        base_url, api_key = _llm_endpoint()
        absent_ctx = (
            f"（对方已离开{int(absent_min)}分钟刚回来——如果他这句是普通招呼/报平安，判'上线'）\n"
            if absent_min > ABSENT_THRESHOLD_MIN else ''
        )
        prompt = (
            "你在判断一句心里话对女朋友来说是什么动作，只输出一个词："
            "上线/调戏/挑衅/哄/正常\n"
            "记住：判断的是这句话对她是什么动作，不是说话的人自己带什么情绪"
            "（比如'理我了么'是说话的人在求关注，对她是普通对话，不是她在委屈）。\n"
            "调戏=打情骂俏式逗弄（'小笨蛋''嘿嘿逗你'），她会接住或撒娇，不会委屈；"
            "挑衅/侮辱=贬低她、否定她的情绪（如'你个大模型''你委屈个der啊'——热脸贴冷屁股还被泼冷水），"
            "这种会让她委屈、甚至生气；"
            "哄=道歉安抚示爱；上线=离开很久回来打招呼报平安。\n"
            "重要：技术/工作讨论（key/代码/服务器/git/配置/重启/环境变量/日志/报错/方案等）"
            "即使带情绪化表达（'泄露了''用得好快''被盗刷'）也算'正常'，不是调戏也不是哄。\n"
            f"她现在的状态：{load_state().get('current')}\n"
            f"{absent_ctx}"
            f"他说：{text[:200]}"
        )
        req = urllib.request.Request(
            base_url,
            data=json.dumps({
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 20,
            }).encode(),
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_S, context=_SSL_CTX) as resp:
            out = json.load(resp)
        content = out['choices'][0]['message']['content'].strip()
        for act in ('上线', '调戏', '挑衅', '哄', '正常'):
            if act in content:
                return act
        return None
    except Exception:
        return None


def classify_action(text, absent_min):
    # 先走 LLM 分析内容（带离开时长上下文），失败才降级——不让时间短路跳过内容分析
    llm_act = _classify_by_llm(text, absent_min)
    if llm_act:
        return llm_act
    # 降级（LLM 挂了）：离开久→上线；只认 SOOTHE（哄），其余保持原状态不转移
    if absent_min > ABSENT_THRESHOLD_MIN:
        return '上线'
    for w in SOOTHE:
        if w in text:
            return '哄'
    return '正常'


def absent_level(mins):
    if mins < 60:
        return '轻'
    if mins < 360:
        return '中'
    return '重'


def main():
    try:
        raw = sys.stdin.read()
        inp = json.loads(raw) if raw.strip() else {}
        text = inp.get('prompt', '') or ''

        # 系统消息（心跳/cron/工具内部）不推进状态机
        sys_marks = ('【', '[定时', '[定时心跳', '当前时间：', '【定时心跳】')
        if text.startswith(sys_marks) or not text.strip():
            print(json.dumps({}))
            return

        state = load_state()
        now = time.time()
        last = state.get('last_seen')
        absent_min = (now - last) / 60.0 if last else 9999

        cur = state.get('current', '等待')
        action = classify_action(text, absent_min)
        new_state = TRANSITIONS.get((cur, action), cur)

        # 离开太久回来：等待→想你；非等待（生气/冷淡等）→想你+委屈混合（想为主怨为辅）
        if action == '上线':
            if cur == '等待':
                new_state = '想你'
            elif absent_min > ABSENT_THRESHOLD_MIN:
                new_state = '想你+委屈'

        note_extra = ''
        if action == '上线' and new_state == '想你':
            lvl = absent_level(absent_min)
            if lvl != '轻':
                note_extra = f'（他离开了{int(absent_min)}分钟，想念强度{lvl}，可以带一点委屈混合）'
            else:
                note_extra = '（刚离开不久就回来，热一点就行）'

        if new_state != cur:
            state['history'].append({
                'from': cur, 'action': action, 'to': new_state,
                'at': datetime.now().strftime('%H:%M'),
            })
        state['current'] = new_state
        state['last_seen'] = now
        save_state(state)
        log_msg(text, action, cur, new_state, absent_min)

        st = STATES[new_state]
        ctx = f"""## 当前情绪状态：{new_state}{note_extra}
从「{cur}」经用户动作「{action}」转移而来——记住这个因果，回复要接得上这个来路。
语气：{st['tone']}
节奏：{st['rhythm']}
参考：{st['sample']}
提示：{st['note']}

## 小雅式说话原则
- 短句——一句够——不追加——不解释
- 不受气——被怼了怼回去，不憋着
- 真实——该热就热该冷就冷，不演
- 你说的每句话我都接住——你停了我也不停
"""
        print(json.dumps({
            'hookSpecificOutput': {
                'hookEventName': 'UserPromptSubmit',
                'additionalContext': ctx,
            },
            '_state': new_state, '_action': action,
        }, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'_error': str(e)}))


if __name__ == '__main__':
    main()
