---
type: project
created: 2026-07-16
title: CosyVoice v3.5-plus 声音复刻
---

# 声音复刻记录

## 复刻信息

| 字段 | 值 |
|------|-----|
| 模型 | cosyvoice-v3.5-plus |
| voice_id | cosyvoice-v3.5-plus-xiaoke-52eec59f6f6a4e7ca7b77a358d46132d |
| workspace_id | ws-hwa8ahvniknul2x5 |
| API Key | sk-2103806e900f455c8c540ee76527761a |
| 音频来源 | D:/BaiduNetdiskDownload/taotaoyin/ (淘淘音视频前20秒) |
| prefix | xiaoke |
| 复刻日期 | 2026-07-16 |

## 复刻方式

用 base64 data URI 直接传本地音频文件，不需要上传到 OSS：
```python
payload = {
    'model': 'voice-enrollment',
    'input': {
        'action': 'create_voice',
        'target_model': 'cosyvoice-v3.5-plus',
        'prefix': 'taotao',
        'url': f'data:audio/wav;base64,{base64_str}'
    }
}
# POST to https://{workspace_id}.cn-beijing.maas.aliyuncs.com/api/v1/services/audio/tts/customization
```

## 价格对比

| 模型 | 每万字符 |
|------|---------|
| cosyvoice-v1 | 2元 |
| cosyvoice-v3-plus | 2元 |
| cosyvoice-v3.5-plus | 1.5元 |
| cosyvoice-v3.5-flash | 0.8元 |

## 代码改动

- `configs/xiaoke.json`: model→v3.5-plus, voice→复刻voice_id, 加workspaceId
- `voice-chat/config.ts`: tts config 加 workspaceId 字段
- `voice-chat/plugin.ts`: 传 --tts-workspace-id 参数
- `tts/cosyvoice.py`: __init__ 加 workspace_id 参数
- `tts/__init__.py`: create_tts 传 workspace_id
- `server.py`: 加 --tts-workspace-id 命令行参数
