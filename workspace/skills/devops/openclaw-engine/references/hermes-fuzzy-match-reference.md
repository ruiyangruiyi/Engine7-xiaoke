# Hermes fuzzy_match.py 参考（小柯翻译用）

**源文件**: `/mnt/d/hermes/hermes-agent/tools/fuzzy_match.py`
**行数**: 704行（含注释docstring）
**纯逻辑**: ~400行Python，TS版预计450-500行

## 9种匹配策略（按顺序尝试）

| # | 策略名 | 说明 | TS版复杂度 |
|---|--------|------|-----------|
| 1 | exact | 精确字符串匹配 | 低 |
| 2 | line_trimmed | 每行strip首尾空白后匹配 | 中 |
| 3 | whitespace_normalized | 折叠多空白为单空格 | 中 |
| 4 | indentation_flexible | 忽略缩进差异 | 中 |
| 5 | escape_normalized | `\n`→真实换行等转义 | 低 |
| 6 | trimmed_boundary | 只trim首尾行的空白 | 低 |
| 7 | unicode_normalized | 智能引号→ASCII、破折号→--等 | 中 |
| 8 | block_anchor | 首行+尾行锚定，中间用SequenceMatcher(阈值0.5/0.7) | 高 |
| 9 | context_aware | 逐行相似度≥0.8，整体≥50%行通过 | 高 |

## 关键辅助函数

- `_apply_replacements(matches, new_string)` — 从后向前替换保持位置
- `_calculate_line_positions(lines, startLine, endLine)` — 行号→字符偏移
- `_find_normalized_matches()` — 归一化后匹配→映射回原位置
- `_map_normalized_positions()` — 归一化字符串位置→原始字符串位置
- `_build_orig_to_norm_map()` — 原始字符→归一化字符索引映射（处理Unicode展开）

## Escape-Drift检测（`_detect_escape_drift`）

非exact匹配时的安全守卫：
- 检测new_string里有没有 `\'` 或 `\"` 这种工具调用序列化伪影
- 如果old_string和new_string都有，但文件实际匹配区域没有 → 阻止写入
- 防止工具调用传输层在引号前插入多余反斜杠，污染源文件

## "Did you mean"提示（`find_closest_lines`）

匹配失败时返回最相似的代码段，帮LLM修正：
- 用第一行做锚点，SequenceMatcher逐行打分
- 阈值>0.3的行收集起来
- 最多返回3个匹配，每个带2行上下文
- `format_no_match_hint()` 组装成 `Did you mean one of these sections?` 格式

## CC edit.ts 当前状态 vs 这个参考

CC的edit.ts只有2阶段匹配（精确+引号规范化），缺失：
- 缺7个模糊匹配策略
- 缺escape-drift检测
- 缺"did you mean"提示
- 缺unicode规范化（智能引号等）

**实现建议**：先加策略2(line_trimmed) + 4(indentation_flexible)覆盖80%场景，escape-drift是安全必加。
