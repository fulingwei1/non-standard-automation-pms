#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D组代码去重脚本
- 添加 db_helpers 导入
- 替换 query+404 模式
- 替换 db.add+commit+refresh+return 模式
"""

import re
import ast
import os
import sys

WORKDIR = "/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms"

FILES = [
    "app/api/v1/endpoints/project_contributions.py",
    "app/api/v1/endpoints/project_review/comparison.py",
    "app/api/v1/endpoints/project_review/knowledge.py",
    "app/api/v1/endpoints/project_review/lessons.py",
    "app/api/v1/endpoints/project_review/reviews.py",
    "app/api/v1/endpoints/project_workspace.py",
    "app/api/v1/endpoints/projects/approvals/action_new.py",
    "app/api/v1/endpoints/projects/approvals/cancel_new.py",
    "app/api/v1/endpoints/projects/costs/allocation.py",
    "app/api/v1/endpoints/projects/costs/analysis.py",
    "app/api/v1/endpoints/projects/costs/forecast.py",
    "app/api/v1/endpoints/projects/evaluations/crud.py",
    "app/api/v1/endpoints/projects/evaluations/custom.py",
    "app/api/v1/endpoints/projects/ext_best_practices.py",
    "app/api/v1/endpoints/projects/ext_reviews.py",
    "app/api/v1/endpoints/projects/machines/crud.py",
    "app/api/v1/endpoints/projects/machines/custom.py",
    "app/api/v1/endpoints/projects/members/crud.py",
    "app/api/v1/endpoints/projects/milestones/crud.py",
    "app/api/v1/endpoints/projects/milestones/workflow.py",
    "app/api/v1/endpoints/projects/progress/summary.py",
    "app/api/v1/endpoints/projects/project_crud.py",
    "app/api/v1/endpoints/projects/resource_plan/assignment.py",
    "app/api/v1/endpoints/projects/resource_plan/crud.py",
    "app/api/v1/endpoints/projects/risks.py",
    "app/api/v1/endpoints/projects/roles/leads.py",
    "app/api/v1/endpoints/projects/roles/team_members.py",
    "app/api/v1/endpoints/projects/schedule_prediction.py",
    "app/api/v1/endpoints/projects/stages/crud.py",
    "app/api/v1/endpoints/projects/stages/node_operations.py",
    "app/api/v1/endpoints/projects/stages/stage_operations.py",
    "app/api/v1/endpoints/projects/stages/status_updates.py",
    "app/api/v1/endpoints/projects/template_versions.py",
    "app/api/v1/endpoints/projects/timesheet/crud.py",
    "app/api/v1/endpoints/purchase/orders_refactored.py",
    "app/api/v1/endpoints/purchase/receipts.py",
    "app/api/v1/endpoints/purchase/requests_refactored.py",
    "app/api/v1/endpoints/purchase_intelligence.py",
    "app/api/v1/endpoints/qualification/assessments.py",
    "app/api/v1/endpoints/qualification/employees.py",
    "app/api/v1/endpoints/qualification/levels.py",
    "app/api/v1/endpoints/qualification/models.py",
    "app/api/v1/endpoints/rd_project/documents.py",
    "app/api/v1/endpoints/rd_project/expenses.py",
    "app/api/v1/endpoints/report_center/generate/download.py",
    "app/api/v1/endpoints/report_center/generate/export.py",
    "app/api/v1/endpoints/report_center/templates.py",
]

IMPORT_LINE = "from app.utils.db_helpers import get_or_404, save_obj, delete_obj"

# Pattern 1: query + 404
# Matches: `<indent><var> = db.query(<Model>).filter(<Model>.<field> == <id_expr>).first()\n<indent>if not <var>:\n<indent>    raise HTTPException(status_code=404, detail="<msg>")`
# Note: [^,\)]+ ensures no comma (single-condition filter only)
PATTERN_404 = re.compile(
    r'^(?P<indent>[ \t]*)(?P<var>\w+)\s*=\s*db\.query\((?P<model>\w+)\)'
    r'\.filter\((?P=model)\.\w+\s*==\s*(?P<id_expr>[^,\)]+)\)\.first\(\)\n'
    r'(?P=indent)if not (?P=var):\n'
    r'(?P=indent)[ \t]+raise HTTPException\(status_code=404,\s*detail=(?P<detail>["\'][^"\']+["\'])\)',
    re.MULTILINE
)

# Pattern 2: db.add + db.commit + db.refresh + return obj (all on consecutive lines, same indent)
PATTERN_SAVE = re.compile(
    r'^(?P<indent>[ \t]*)db\.add\((?P<obj>\w+)\)\n'
    r'(?P=indent)db\.commit\(\)\n'
    r'(?P=indent)db\.refresh\((?P=obj)\)\n'
    r'(?P=indent)return (?P=obj)',
    re.MULTILINE
)

def check_syntax(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True
    except SyntaxError as e:
        print(f"  [SYNTAX ERROR] {e}")
        return False

def add_import(content):
    """在顶层 import 区域末尾添加 db_helpers 导入（跳过缩进/多行 import 内部行）"""
    if IMPORT_LINE in content:
        return content, False
    
    lines = content.split('\n')
    last_import_idx = -1
    in_multiline_import = False
    
    for i, line in enumerate(lines):
        # 只处理顶层（无缩进）的 import/from 行
        if not line.startswith((' ', '\t')):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                last_import_idx = i
                # 检查是否是多行 import（含未闭合括号）
                if '(' in stripped and ')' not in stripped:
                    in_multiline_import = True
            elif in_multiline_import:
                # 在多行 import 的闭合行
                if stripped == ')' or stripped.endswith(')'):
                    in_multiline_import = False
                    last_import_idx = i
        elif in_multiline_import:
            # 多行 import 内部的续行，更新 last_import_idx 到当前行（包括闭合括号行）
            if ')' in line:
                last_import_idx = i
                in_multiline_import = False
    
    if last_import_idx >= 0:
        lines.insert(last_import_idx + 1, IMPORT_LINE)
        return '\n'.join(lines), True
    else:
        # 文件没有 import，在开头添加
        return IMPORT_LINE + '\n' + content, True

def replace_404_pattern(content):
    """替换 query+404 模式"""
    count = 0
    
    def replacer(m):
        nonlocal count
        indent = m.group('indent')
        var = m.group('var')
        model = m.group('model')
        id_expr = m.group('id_expr').strip()
        detail = m.group('detail')
        count += 1
        return f'{indent}{var} = get_or_404(db, {model}, {id_expr}, {detail})'
    
    new_content = PATTERN_404.sub(replacer, content)
    return new_content, count

def replace_save_pattern(content):
    """替换 db.add+commit+refresh+return 模式"""
    count = 0
    
    def replacer(m):
        nonlocal count
        indent = m.group('indent')
        obj = m.group('obj')
        count += 1
        return f'{indent}return save_obj(db, {obj})'
    
    new_content = PATTERN_SAVE.sub(replacer, content)
    return new_content, count

def process_file(rel_path):
    filepath = os.path.join(WORKDIR, rel_path)
    
    if not os.path.exists(filepath):
        print(f"  [SKIP] File not found: {filepath}")
        return {'file': rel_path, 'status': 'not_found', 'import_added': False, 'p1': 0, 'p2': 0}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    content = original
    
    # Step 1: 替换 pattern 1 (404)
    content, p1_count = replace_404_pattern(content)
    
    # Step 2: 替换 pattern 2 (save)
    content, p2_count = replace_save_pattern(content)
    
    # Step 3: 添加 import (如果有替换或者需要)
    import_added = False
    if p1_count > 0 or p2_count > 0:
        content, import_added = add_import(content)
    
    # 如果没有任何变化，跳过
    if content == original:
        print(f"  [NO CHANGE] {rel_path}")
        return {'file': rel_path, 'status': 'no_change', 'import_added': False, 'p1': 0, 'p2': 0}
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 检查语法
    if check_syntax(filepath):
        print(f"  [OK] {rel_path} | p1={p1_count} p2={p2_count} import={'yes' if import_added else 'already'}")
        return {'file': rel_path, 'status': 'ok', 'import_added': import_added, 'p1': p1_count, 'p2': p2_count}
    else:
        # 回滚
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(original)
        print(f"  [ROLLBACK] {rel_path} - syntax error, reverted")
        return {'file': rel_path, 'status': 'rollback', 'import_added': False, 'p1': 0, 'p2': 0}

def main():
    os.chdir(WORKDIR)
    
    results = []
    total_p1 = 0
    total_p2 = 0
    
    for rel_path in FILES:
        print(f"Processing: {rel_path}")
        result = process_file(rel_path)
        results.append(result)
        total_p1 += result['p1']
        total_p2 += result['p2']
    
    print(f"\n=== Summary ===")
    print(f"Total files processed: {len(FILES)}")
    print(f"Pattern1 (query+404) replacements: {total_p1}")
    print(f"Pattern2 (save_obj) replacements: {total_p2}")
    
    return results, total_p1, total_p2

if __name__ == '__main__':
    results, total_p1, total_p2 = main()
    
    # Print detailed results
    ok = [r for r in results if r['status'] == 'ok']
    no_change = [r for r in results if r['status'] == 'no_change']
    rollback = [r for r in results if r['status'] == 'rollback']
    not_found = [r for r in results if r['status'] == 'not_found']
    
    print(f"\nOK: {len(ok)}")
    print(f"No change: {len(no_change)}")
    print(f"Rollback: {len(rollback)}")
    print(f"Not found: {len(not_found)}")
