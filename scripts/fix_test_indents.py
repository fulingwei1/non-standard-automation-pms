#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试修复测试文件中因批处理脚本导致的缩进丢失：
- 识别以 for/if/with/try/elif/else/while/class/def 开头且以 : 结束的行
- 若其后的有效行缩进不足，则自动补齐 4 个空格
"""

from pathlib import Path
from typing import List

CONTROL_FLOW_PREFIXES = (
    "for ",
    "if ",
    "elif ",
    "else:",
    "while ",
    "with ",
    "try:",
    "except",
    "finally:",
    "class ",
    "def ",
)

BLOCK_END_KEYWORDS = (
    "except",
    "elif",
    "else",
    "finally",
    "class",
    "def",
    "@",
)


def should_adjust_block(line: str) -> bool:
    stripped = line.lstrip()
    if not stripped:
        return False
    if not stripped.rstrip().endswith(":"):
        return False
    for prefix in CONTROL_FLOW_PREFIXES:
        if stripped.startswith(prefix):
            return True
    return False


def is_block_end(line: str, base_indent: int) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    leading = len(line) - len(line.lstrip())
    if leading > base_indent:
        return False
    token = stripped.split()[0]
    token = token.rstrip(":")
    if token in BLOCK_END_KEYWORDS:
        return True
    if stripped.startswith("@"):
        return True
    return False


def fix_lines(lines: List[str]) -> List[str]:
    i = 0
    total = len(lines)
    while i < total:
        line = lines[i]
        if should_adjust_block(line):
            base_indent = len(line) - len(line.lstrip())
            expected_indent = base_indent + 4
            j = i + 1
            while j < total:
                current = lines[j]
                stripped = current.strip()
                if not stripped:
                    j += 1
                    continue
                leading = len(current) - len(current.lstrip())
                if leading > base_indent:
                    # 已经有更深缩进，说明块内正常
                    break
                if is_block_end(current, base_indent):
                    break
                # 调整缩进
                lines[j] = " " * expected_indent + current.lstrip()
                j += 1
        i += 1
    return lines


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8").splitlines(keepends=True)
    fixed = fix_lines(original[:])
    if fixed != original:
        path.write_text("".join(fixed), encoding="utf-8")
        return True
    return False


def main():
    base_dir = Path("tests/unit")
    changed = 0
    for file_path in sorted(base_dir.rglob("*.py")):
        if process_file(file_path):
            changed += 1
            print(f"Fixed indentation: {file_path}")
    print(f"Completed. Updated {changed} files.")


if __name__ == "__main__":
    main()
