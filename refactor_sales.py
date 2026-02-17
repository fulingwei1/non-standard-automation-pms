#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量重构 sales 模块重复 CRUD 代码
"""

import re
import os
import sys
from pathlib import Path

# 统计
stats = {
    "files_processed": 0,
    "files_modified": 0,
    "rule1_replacements": 0,  # get_or_404
    "rule2_replacements": 0,  # save_obj
    "rule3_replacements": 0,  # delete_obj
}

# 规则1：标准单ID查询+404
RULE1_PATTERN = re.compile(
    r'([ \t]*)'
    r'(\w+)\s*=\s*'
    r'db\.query\((\w+)\)\.filter\(\3\.id\s*==\s*(\w+)\)\.first\(\)'
    r'[ \t]*\n'
    r'\1if\s+not\s+\2\s*:[ \t]*\n'
    r'[ \t]+raise\s+HTTPException\(\s*status_code\s*=\s*404\s*,\s*detail\s*=\s*'
    r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
    r'\s*\)',
    re.MULTILINE
)

# 规则2：add+commit+refresh
RULE2_PATTERN = re.compile(
    r'([ \t]*)db\.add\((\w+)\)[ \t]*\n'
    r'\1db\.commit\(\)[ \t]*\n'
    r'\1db\.refresh\(\2\)',
    re.MULTILINE
)

# 规则3：delete+commit
RULE3_PATTERN = re.compile(
    r'([ \t]*)db\.delete\((\w+)\)[ \t]*\n'
    r'\1db\.commit\(\)',
    re.MULTILINE
)


def apply_rule1(content):
    count = [0]

    def replacer(m):
        count[0] += 1
        indent = m.group(1)
        var = m.group(2)
        model = m.group(3)
        id_var = m.group(4)
        detail = m.group(5)
        return f'{indent}{var} = get_or_404(db, {model}, {id_var}, detail={detail})'

    new_content = RULE1_PATTERN.sub(replacer, content)
    return new_content, count[0]


def apply_rule2(content):
    count = [0]

    def replacer(m):
        count[0] += 1
        indent = m.group(1)
        var = m.group(2)
        return f'{indent}save_obj(db, {var})'

    new_content = RULE2_PATTERN.sub(replacer, content)
    return new_content, count[0]


def apply_rule3(content):
    count = [0]

    def replacer(m):
        count[0] += 1
        indent = m.group(1)
        var = m.group(2)
        return f'{indent}delete_obj(db, {var})'

    new_content = RULE3_PATTERN.sub(replacer, content)
    return new_content, count[0]


def find_last_import_end(content):
    """
    找到最后一个 import 块的结束位置（正确处理多行 import）。
    返回字符偏移量，指向最后一个 import 块结尾（含换行符）。
    """
    lines = content.splitlines(keepends=True)
    last_import_end = -1
    pos = 0
    in_import_block = False
    import_block_start = -1

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not in_import_block:
            if stripped.startswith('from ') or stripped.startswith('import '):
                in_import_block = True
                import_block_start = pos
                # 检查是否是单行 import（无括号或括号在同一行关闭）
                if '(' not in line or ')' in line:
                    in_import_block = False
                    last_import_end = pos + len(line)
        else:
            # 在多行 import 块中，等待 )
            if ')' in line:
                in_import_block = False
                last_import_end = pos + len(line)
        pos += len(line)

    return last_import_end


def update_imports(content, needs_get_or_404, needs_save_obj, needs_delete_obj):
    """更新 import 语句：合并或插入 db_helpers import"""
    if not (needs_get_or_404 or needs_save_obj or needs_delete_obj):
        return content

    needed = []
    if needs_get_or_404:
        needed.append("get_or_404")
    if needs_save_obj:
        needed.append("save_obj")
    if needs_delete_obj:
        needed.append("delete_obj")

    # 检查是否已有 db_helpers import
    existing_pattern = re.compile(
        r'^from\s+app\.utils\.db_helpers\s+import\s+(.+)$',
        re.MULTILINE
    )
    existing_match = existing_pattern.search(content)

    if existing_match:
        # 合并已有 import
        existing_names = [n.strip() for n in existing_match.group(1).split(',')]
        all_names = sorted(set(existing_names + needed))
        new_import = f"from app.utils.db_helpers import {', '.join(all_names)}"
        content = content[:existing_match.start()] + new_import + content[existing_match.end():]
    else:
        # 在最后一个 import 块（含多行）之后插入
        insert_after = find_last_import_end(content)

        new_import = f"from app.utils.db_helpers import {', '.join(needed)}\n"
        if insert_after >= 0:
            content = content[:insert_after] + new_import + content[insert_after:]
        else:
            content = new_import + content

    return content


def process_file(filepath):
    """处理单个文件"""
    stats["files_processed"] += 1

    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    content = original

    content, c1 = apply_rule1(content)
    content, c2 = apply_rule2(content)
    content, c3 = apply_rule3(content)

    total_changes = c1 + c2 + c3
    if total_changes == 0:
        return

    # 更新 import
    content = update_imports(content, c1 > 0, c2 > 0, c3 > 0)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    stats["files_modified"] += 1
    stats["rule1_replacements"] += c1
    stats["rule2_replacements"] += c2
    stats["rule3_replacements"] += c3

    print(f"  ✓ {os.path.relpath(filepath)}: rule1={c1}, rule2={c2}, rule3={c3}")


def main():
    sales_dir = Path("app/api/v1/endpoints/sales")
    if not sales_dir.exists():
        print(f"❌ 目录不存在: {sales_dir}")
        sys.exit(1)

    py_files = sorted(sales_dir.rglob("*.py"))
    print(f"📂 找到 {len(py_files)} 个 Python 文件\n")

    for f in py_files:
        process_file(f)

    total = stats['rule1_replacements'] + stats['rule2_replacements'] + stats['rule3_replacements']
    print(f"""
========= 重构完成 =========
  处理文件: {stats['files_processed']}
  修改文件: {stats['files_modified']}
  规则1 (get_or_404): {stats['rule1_replacements']} 处
  规则2 (save_obj):   {stats['rule2_replacements']} 处
  规则3 (delete_obj): {stats['rule3_replacements']} 处
  总替换:  {total} 处
===========================
""")


if __name__ == "__main__":
    main()
