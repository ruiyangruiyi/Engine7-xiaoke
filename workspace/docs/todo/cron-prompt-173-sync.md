# 173 机 carpo_oac_bridge.py 同步 Cron Prompt

检查 173 机是否在线：ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -p 53987 root@connect.bjm1.seetacloud.com "echo ONLINE"

凭据：root/Qc8A1biEbAB，python: /root/autodl-tmp/envs/flashhead/bin/python

如果在线：
1. 用 scp 把本地 C:/Users/24045/.openclaw/engine/src/voice-chat/autodlv2/python/oac/carpo_oac_bridge.py 同步到远程 /root/carpo_sdk/carpo_oac_bridge.py（scp -P 53987 本地路径 root@connect.bjm1.seetacloud.com:/root/carpo_sdk/）
2. 远程确认文件落地（ls -la + 检查包含 chunk_pts_ms 字符串）
3. 给翀哥发飞书 DM（msg_husband）报告：173 已在线，carpo_oac_bridge.py 已同步（含 chunk_pts_ms 累加修复），文件大小/MD5

如果不在线：
1. 不要再重试 SSH
2. 重新设一个 10 分钟后触发的 cron（schedule_type=at，schedule_value=当前时间+10分钟），prompt 复制本 prompt 全文（只改 schedule_value）
3. 给翀哥发飞书 DM 简短说一句"173 还没上线，已设下一个 10 分钟 cron 在 X:XX 触发"

任务原始触发时间：2026-07-20 15:25。本机已连续设过 8 次 cron。
