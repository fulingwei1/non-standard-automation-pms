# -*- coding: utf-8 -*-
"""中文友好的轻量文本相似度（详#16 短期方案，无外部依赖）。

背景：sentence-transformers 未安装时，旧回退是"空格分词 Jaccard"（中文无空格恒 0）
和"单字符哈希袋向量"（语序不敏感，且内建 hash() 跨进程随机化导致存量向量失配）。
本模块提供：中文字符 bigram + 英文/数字词元的计数向量余弦相似度，
以及跨进程稳定的词元哈希。真向量方案（qwen embedding）待标准百炼密钥后升级。
"""
import hashlib
import math
import re
from collections import Counter
from typing import Dict, List

_TOKEN_RE = re.compile(r"[a-z0-9_]+|[一-鿿]+")


def tokenize(text: str) -> List[str]:
    """归一化词元：英文/数字整词 + 中文连续段拆 bigram（单字段保留单字）。"""
    tokens: List[str] = []
    for match in _TOKEN_RE.findall((text or "").lower()):
        if match[0].isascii():
            tokens.append(match)
            continue
        if len(match) == 1:
            tokens.append(match)
            continue
        tokens.extend(match[i : i + 2] for i in range(len(match) - 1))
    return tokens


def token_counts(text: str) -> Dict[str, int]:
    return dict(Counter(tokenize(text)))


def cosine_similarity(text1: str, text2: str) -> float:
    """bigram 计数向量余弦相似度，范围 [0, 1]。"""
    c1, c2 = token_counts(text1), token_counts(text2)
    if not c1 or not c2:
        return 0.0
    dot = sum(v * c2[k] for k, v in c1.items() if k in c2)
    norm1 = math.sqrt(sum(v * v for v in c1.values()))
    norm2 = math.sqrt(sum(v * v for v in c2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def stable_token_hash(token: str, dim: int) -> int:
    """跨进程稳定的词元哈希（内建 hash() 有进程级随机化，不可用于持久化向量）。"""
    digest = hashlib.md5(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % dim
