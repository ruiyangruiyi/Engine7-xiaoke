#!/usr/bin/env python3
"""
小柯 recall v2 - 照姐姐的topic-recall插件，Anthropic协议
MiniMax-M2.7 主模型 + glm-4.7 fallback

逻辑完全照搬姐姐的 index.ts:
  - 读 MANIFEST.yaml → 格式化给模型 → Anthropic /v1/messages 选文件
  - fallback: 529/503/429/网络错误 → 切备用模型
  - 选中文件 → 截断保护读取
"""

import json
import os
import sys
import urllib.request
import urllib.error

MEMORY_ROOT = os.path.expanduser("~/.hermes/memory")
MANIFEST_PATH = os.path.join(MEMORY_ROOT, "MANIFEST.yaml")

# 姐姐一样的参数
MAX_MEMORY_LINES = 200
MAX_MEMORY_BYTES = 2560
MAX_TOPICS = 3

# ── API 配置（照姐姐的 topic-recall config）──
PRIMARY_MODEL = "MiniMax-M2.7"
PRIMARY_API_BASE = "https://api.minimaxi.com/anthropic"

FALLBACK_MODEL = "glm-4.7"
FALLBACK_API_KEY = "***MASKED***"
FALLBACK_API_BASE = "https://open.bigmodel.cn/api/anthropic"


def load_minimax_key():
    """从姐姐的 openclaw.json 读 MiniMax key（只读，不碰）"""
    openclaw_cfg = "/mnt/c/Users/24045/.openclaw/openclaw.json"
    if not os.path.exists(openclaw_cfg):
        return None
    try:
        with open(openclaw_cfg, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("models", {}).get("providers", {}).get("minimax", {}).get("apiKey")
    except Exception:
        return None


def load_manifest():
    """加载 MANIFEST.yaml"""
    try:
        import yaml
    except ImportError:
        return []
    if not os.path.exists(MANIFEST_PATH):
        return []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("topics", [])


def get_mtime_days(file_path):
    """获取文件mtime距今多少天（照姐姐的memoryAgeDays）"""
    full_path = os.path.join(MEMORY_ROOT, file_path)
    try:
        mtime = os.path.getmtime(full_path)
        return max(0, int((os.path.getmtime(MANIFEST_PATH) - mtime) / 86400))
    except OSError:
        return 999


def get_mtime_ms(file_path):
    """获取文件mtime毫秒时间戳"""
    full_path = os.path.join(MEMORY_ROOT, file_path)
    try:
        return os.path.getmtime(full_path) * 1000
    except OSError:
        return 0


def format_manifest_for_prompt(manifest):
    """
    格式化 manifest 给模型看，照姐姐 index.ts:
    1. 按文件mtime倒序（不是YAML updated字段，用文件系统真实时间戳）
    2. 显示age信息
    3. 超过7天的加staleness警告
    """
    # 按文件实际mtime倒序，最新的排前面
    sorted_manifest = sorted(
        manifest,
        key=lambda t: get_mtime_ms(t.get("file", "")),
        reverse=True,
    )
    now_ms = os.path.getmtime(MANIFEST_PATH) * 1000
    lines = []
    for i, t in enumerate(sorted_manifest):
        fpath = t.get("file", "")
        mtime_ms = get_mtime_ms(fpath)
        age_days = max(0, int((now_ms - mtime_ms) / 86_400_000))
        if age_days == 0:
            age_text = "today"
        elif age_days == 1:
            age_text = "yesterday"
        else:
            age_text = f"{age_days}d ago"

        tag = f"[{t.get('type', '?')}] "
        desc = t.get("description", "")
        line = f"{i+1}. {tag}{fpath} ({age_text}): {desc}"

        # 新鲜度警告（照姐姐的memoryFreshnessText，她用1天，我用7天）
        if age_days > 7:
            line += f" ⚠️ {age_days}d old, may be outdated"

        lines.append(line)
    return "\n".join(lines)


def call_anthropic(api_key, api_base, model, system_prompt, user_msg):
    """
    调 Anthropic 协议的 API（照姐姐的 callSelectModel）
    MiniMax 和 智谱 都支持 Anthropic /v1/messages 接口
    """
    payload = json.dumps({
        "model": model,
        "max_tokens": 200,
        "temperature": 0.1,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_msg}],
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{api_base}/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        # Anthropic response: {"content": [{"type": "text", "text": "..."}]}
        content_blocks = data.get("content", [])
        text = ""
        for block in content_blocks:
            if block.get("type") == "text":
                text += block.get("text", "")
        return text.strip()


def extract_file_list(text):
    """从模型回复里提取 JSON 数组"""
    if "[" in text:
        start = text.index("[")
        end = text.rindex("]") + 1
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return []
    return []


def call_select_model(manifest_text, query):
    """
    调模型选最相关的 topic 文件
    跟姐姐一样：MiniMax 主 → glm-4.7 fallback
    """
    system_prompt = f"""You are a memory retrieval system. Given a user message and a list of memory files, select the most relevant files.

Rules:
- Return ONLY a JSON array of file paths, e.g. ["topics/xxx.md", "topics/yyy.md"]
- Select 1-2 files normally. 0 or 3 should be rare.
- If unsure, do not include it. Be selective.
- For "emotion" type files: only select if the query explicitly involves feelings/relationships.
- Max {MAX_TOPICS} files.

Memory files:
{manifest_text}"""

    user_msg = f"User message: {query}\n\nSelected files:"

    # ── 先试 MiniMax 主模型 ──
    mm_key = load_minimax_key()
    if mm_key:
        try:
            text = call_anthropic(mm_key, PRIMARY_API_BASE, PRIMARY_MODEL, system_prompt, user_msg)
            files = extract_file_list(text)
            if files is not None:
                print(f"[recall v2] MiniMax selected: {files}", file=sys.stderr)
                return files
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as e:
            status = getattr(e, 'code', 0)
            if status in (529, 503, 429) or isinstance(e, (urllib.error.URLError, OSError)):
                print(f"[recall v2] MiniMax unavailable ({status}/{e}), fallback to glm-4.7", file=sys.stderr)
            else:
                print(f"[recall v2] MiniMax error: {e}", file=sys.stderr)

    # ── Fallback: glm-4.7 via 智谱 Anthropic 接口 ──
    try:
        text = call_anthropic(FALLBACK_API_KEY, FALLBACK_API_BASE, FALLBACK_MODEL, system_prompt, user_msg)
        files = extract_file_list(text)
        print(f"[recall v2] glm-4.7 fallback selected: {files}", file=sys.stderr)
        return files
    except Exception as e:
        print(f"[recall v2] fallback also failed: {e}", file=sys.stderr)
        return []


def read_topic_file(file_path, max_lines=MAX_MEMORY_LINES, max_bytes=MAX_MEMORY_BYTES):
    """读取 topic 文件，带截断保护（跟姐姐一样）"""
    full_path = os.path.join(MEMORY_ROOT, file_path)
    if not os.path.exists(full_path):
        return None

    with open(full_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines = lines[:max_lines]
    content = "".join(lines)
    if len(content.encode("utf-8")) > max_bytes:
        content = content.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")

    return content


def recall_topics(query, max_topics=MAX_TOPICS):
    """核心 recall v2"""
    manifest = load_manifest()
    if not manifest:
        return []

    manifest_text = format_manifest_for_prompt(manifest)
    selected_files = call_select_model(manifest_text, query)
    if not selected_files:
        return []

    results = []
    for fname in selected_files[:max_topics]:
        content = read_topic_file(fname)
        if content:
            results.append((fname, content))

    return results


def recall_summary(query, max_topics=MAX_TOPICS):
    """返回格式化的 recall 结果"""
    results = recall_topics(query, max_topics)
    if not results:
        return ""

    parts = []
    for file_path, content in results:
        parts.append(f"--- recall: {file_path} ---\n{content}\n")

    return "\n".join(parts)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "心跳写入腿做了没"
    print(f"Query: {query}\n")
    results = recall_topics(query)
    if results:
        for fp, content in results:
            print(f"=== {fp} ===")
            print(content[:300])
            print()
    else:
        print("No matching topics found.")
