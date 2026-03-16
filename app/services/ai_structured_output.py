"""
Helpers for parsing structured AI outputs.
"""

import json
import re
from typing import Any, Optional


_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def extract_json_payload(content: str) -> Optional[Any]:
    """Best-effort parse for JSON returned by an LLM."""
    if not content:
        return None

    text = content.strip()
    candidates = []

    for block in _CODE_BLOCK_RE.findall(text):
        block = block.strip()
        if block:
            candidates.append(block)

    candidates.append(text)

    object_start = text.find("{")
    object_end = text.rfind("}")
    if object_start != -1 and object_end > object_start:
        candidates.append(text[object_start : object_end + 1])

    array_start = text.find("[")
    array_end = text.rfind("]")
    if array_start != -1 and array_end > array_start:
        candidates.append(text[array_start : array_end + 1])

    seen = set()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    return None
