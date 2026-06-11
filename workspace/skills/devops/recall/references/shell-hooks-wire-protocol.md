# Hermes Shell Hooks Wire Protocol — Recall Hook Reference

## stdin Payload Format (框架→脚本)

框架的 `shell_hooks._serialize_payload()` 构造的JSON：

```json
{
  "hook_event_name": "pre_llm_call",
  "tool_name": null,
  "tool_input": null,
  "session_id": "20260510_050713_6ba199b5",
  "cwd": "/home/chong",
  "extra": {
    "user_message": "用户原始消息",
    "conversation_history": [],
    "is_first_turn": false,
    "model": "glm-5.1",
    "platform": "feishu",
    "sender_id": "ou_123"
  }
}
```

**关键：`user_message` 在 `extra` 字典里，不在顶层！**

原因：`_TOP_LEVEL_PAYLOAD_KEYS = {"tool_name", "args", "session_id", "parent_session_id"}`，
只有这四个key放顶层，其他所有kwargs都塞进 `extra`。

## stdout Response Format (脚本→框架)

```json
// 注入context
{"context": "要注入的文本"}

// 无操作（不注入任何东西）
{"context": ""}

// 或直接不输出/输出非JSON——都被忽略
```

## 诊断命令

```bash
# 检查所有hook健康状态
hermes hooks doctor

# 用合成的payload测试hook（注意payload格式要模拟真实格式）
hermes hooks test pre_llm_call

# 手动模拟框架传参测试
echo '{"hook_event_name":"pre_llm_call","tool_name":null,"tool_input":null,"session_id":"test","cwd":"/home/chong","extra":{"user_message":"测试消息","is_first_turn":true,"model":"glm-5.1","platform":"feishu"}}' | ~/.hermes/scripts/recall_hook.sh
```

## 踩坑记录

| 问题 | 症状 | 解决 |
|------|------|------|
| user_message在extra里 | hook返回空context | 从 `d['extra']['user_message']` 读 |
| 无匹配时返回非空文本 | "No matching topics found"被注入到对话 | grep过滤掉 |
| 成功执行无日志 | 无法确认hook是否在跑 | 用 `hermes hooks test` 验证 |
| hooks_auto_accept未设 | gateway启动时hook被skip | config.yaml设 `hooks_auto_accept: true` |
| 改了脚本没生效 | 不需要重启gateway | 脚本每次fork新子进程，改了就生效 |

## 源码位置

- 序列化：`agent/shell_hooks.py:465-481` (`_serialize_payload`)
- 顶层key定义：`agent/shell_hooks.py:360` (`_TOP_LEVEL_PAYLOAD_KEYS`)
- 回调构造：`agent/shell_hooks.py:421-462` (`_make_callback`)
- 调用点：`run_agent.py:11066-11100` (pre_llm_call hook)
- 注入点：`run_agent.py:11296-11316` (context注入到用户消息)
- Gateway注册：`gateway/run.py:3102-3110`
