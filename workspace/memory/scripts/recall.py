#!/usr/bin/env python3
"""
小柯轻量级recall - 读取腿
照着姐姐的topic-recall，但不用子agent，直接在当前对话里快速匹配。

用法（从skill或对话中调用）：
  from recall import recall_topics
  result = recall_topics("用户消息内容", max_topics=3)
  # result = [(file_path, content), ...]
"""

import yaml
import os
import re

MEMORY_ROOT = os.path.expanduser("~/.hermes/memory")
MANIFEST_PATH = os.path.join(MEMORY_ROOT, "MANIFEST.yaml")
TOPICS_DIR = os.path.join(MEMORY_ROOT, "topics")

# 跟姐姐一样的限制参数
MAX_MEMORY_LINES = 200
MAX_MEMORY_BYTES = 2560
MAX_TOPICS = 3


def load_manifest():
    """加载MANIFEST.yaml"""
    if not os.path.exists(MANIFEST_PATH):
        return []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("topics", [])


def tokenize(text):
    """简单的中文+英文分词"""
    # 中文按字/词（2-4字），英文按空格
    tokens = set()
    # 英文单词
    en_words = re.findall(r'[a-zA-Z]{2,}', text.lower())
    tokens.update(en_words)
    # 中文：提取连续中文字符，然后做2-gram和3-gram
    cn_chunks = re.findall(r'[\u4e00-\u9fff]+', text)
    for chunk in cn_chunks:
        if len(chunk) >= 2:
            for i in range(len(chunk) - 1):
                tokens.add(chunk[i:i+2])  # 2-gram
            if len(chunk) >= 3:
                for i in range(len(chunk) - 2):
                    tokens.add(chunk[i:i+3])  # 3-gram
        tokens.add(chunk)  # 整个词也加
    return tokens


def score_topic(query_tokens, topic):
    """给单个topic打分"""
    score = 0
    
    # 匹配keywords
    topic_keywords = topic.get("keywords", [])
    for kw in topic_keywords:
        kw_lower = kw.lower()
        for qt in query_tokens:
            if qt in kw_lower or kw_lower in qt:
                score += 2
    
    # 匹配description
    desc = topic.get("description", "").lower()
    for qt in query_tokens:
        if qt in desc:
            score += 1
    
    # 匹配name
    name = topic.get("name", "").lower()
    for qt in query_tokens:
        if qt in name:
            score += 1
    
    return score


def read_topic_file(file_path, max_lines=MAX_MEMORY_LINES, max_bytes=MAX_MEMORY_BYTES):
    """读取topic文件，带截断保护（跟姐姐一样）"""
    full_path = os.path.join(MEMORY_ROOT, file_path)
    if not os.path.exists(full_path):
        return None
    
    with open(full_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 截断
    lines = lines[:max_lines]
    content = "".join(lines)
    if len(content.encode("utf-8")) > max_bytes:
        content = content.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
    
    return content


def recall_topics(query, max_topics=MAX_TOPICS):
    """
    核心recall函数
    
    Args:
        query: 用户消息/查询内容
        max_topics: 最多返回几个topic
    
    Returns:
        list of (file_path, content) - 按相关性排序
    """
    manifest = load_manifest()
    if not manifest:
        return []
    
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    
    # 给每个topic打分
    scored = [(score_topic(query_tokens, t), t) for t in manifest]
    # 按分数排序，只取>0的
    scored = [(s, t) for s, t in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # 取前N个
    results = []
    for score, topic in scored[:max_topics]:
        file_path = topic.get("file", "")
        content = read_topic_file(file_path)
        if content:
            results.append((file_path, content))
    
    return results


def recall_summary(query, max_topics=MAX_TOPICS):
    """
    返回精简的recall结果摘要（用于快速注入上下文）
    
    Returns:
        str: 格式化的recall结果
    """
    results = recall_topics(query, max_topics)
    if not results:
        return ""
    
    parts = []
    for file_path, content in results:
        parts.append(f"--- recall: {file_path} ---\n{content}\n")
    
    return "\n".join(parts)


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "翀哥 香港 出差"
    print(f"Query: {query}\n")
    results = recall_topics(query)
    if results:
        for fp, content in results:
            print(f"=== {fp} ===")
            print(content[:200])
            print()
    else:
        print("No matching topics found.")
