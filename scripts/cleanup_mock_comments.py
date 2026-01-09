#!/usr/bin/env python3
"""
批量清理 React/JSX 中残留的 mock/演示 block 注释，避免 /* ... */ 与 JSX 结构冲突。

使用方式：
    python scripts/cleanup_mock_comments.py [root_dir]

不传 root_dir 时默认扫描 frontend/src。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 默认扫描目录
DEFAULT_TARGET = Path("frontend/src")
# 匹配 block 注释的正则
BLOCK_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
# 关键字：命中后判定为 mock 注释并删除
KEYWORDS = ("mock", "Mock", "演示", "demo")


def should_remove(comment: str) -> bool:
    """判断注释块是否包含 mock/演示等关键字。"""
    return any(keyword in comment for keyword in KEYWORDS)


def cleanup_file(file_path: Path) -> int:
    """清理单个文件，返回删除的注释数量。"""
    original_text = file_path.read_text(encoding="utf-8")

    def replacer(match: re.Match[str]) -> str:
        block = match.group(0)
        return "" if should_remove(block) else block

    cleaned_text, removed_count = BLOCK_COMMENT_PATTERN.subn(replacer, original_text)
    if removed_count and cleaned_text != original_text:
        file_path.write_text(cleaned_text, encoding="utf-8")
    return removed_count


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET
    if not root.exists():
        print(f"[WARN] 目录不存在：{root}")
        sys.exit(1)

    total_removed = 0
    scanned_files = 0
    for file_path in root.rglob("*.jsx"):
        scanned_files += 1
        total_removed += cleanup_file(file_path)

    print(f"[DONE] 已扫描 {scanned_files} 个 JSX 文件，移除 {total_removed} 个 mock block 注释。")


if __name__ == "__main__":
    main()
