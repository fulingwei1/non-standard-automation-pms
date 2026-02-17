#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E组代码去重自动化脚本
处理 sales/service/staff/task/timesheet/users 等模块
"""

import re
import ast
import os
import sys
from pathlib import Path

BASE_DIR = Path("/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms")

FILES = [
    "app/api/v1/endpoints/sales/ai_clarifications.py",
    "app/api/v1/endpoints/sales/contacts.py",
    "app/api/v1/endpoints/sales/contracts/approval.py",
    "app/api/v1/endpoints/sales/contracts/basic.py",
    "app/api/v1/endpoints/sales/contracts/contracts.py",
    "app/api/v1/endpoints/sales/contracts/enhanced.py",
    "app/api/v1/endpoints/sales/cost_reminder.py",
    "app/api/v1/endpoints/sales/customer_tags.py",
    "app/api/v1/endpoints/sales/customers.py",
    "app/api/v1/endpoints/sales/health.py",
    "app/api/v1/endpoints/sales/information_gap.py",
    "app/api/v1/endpoints/sales/invoices/basic.py",
    "app/api/v1/endpoints/sales/invoices/workflow.py",
    "app/api/v1/endpoints/sales/opportunity_crud.py",
    "app/api/v1/endpoints/sales/payments/payment_records.py",
    "app/api/v1/endpoints/sales/priority.py",
    "app/api/v1/endpoints/sales/quote_approval.py",
    "app/api/v1/endpoints/sales/quote_exports.py",
    "app/api/v1/endpoints/sales/quote_items.py",
    "app/api/v1/endpoints/sales/quote_quotes_crud.py",
    "app/api/v1/endpoints/sales/quote_templates.py",
    "app/api/v1/endpoints/sales/quote_versions.py",
    "app/api/v1/endpoints/sales/requirement_details.py",
    "app/api/v1/endpoints/sales/templates/contract_templates.py",
    "app/api/v1/endpoints/sales/templates/quote_templates.py",
    "app/api/v1/endpoints/sales/workflows.py",
    "app/api/v1/endpoints/scheduler/configs.py",
    "app/api/v1/endpoints/scheduler/status.py",
    "app/api/v1/endpoints/service/communications.py",
    "app/api/v1/endpoints/service/knowledge/crud.py",
    "app/api/v1/endpoints/service/knowledge/download.py",
    "app/api/v1/endpoints/service/knowledge/interactions.py",
    "app/api/v1/endpoints/service/records.py",
    "app/api/v1/endpoints/service/survey_templates.py",
    "app/api/v1/endpoints/service/surveys.py",
    "app/api/v1/endpoints/service/tickets/assignment.py",
    "app/api/v1/endpoints/service/tickets/crud.py",
    "app/api/v1/endpoints/service/tickets/issues.py",
    "app/api/v1/endpoints/service/tickets/status.py",
    "app/api/v1/endpoints/shortage/analytics/dashboard.py",
    "app/api/v1/endpoints/solution_credits/admin.py",
    "app/api/v1/endpoints/solution_credits/user.py",
    "app/api/v1/endpoints/staff_matching/evaluations.py",
    "app/api/v1/endpoints/staff_matching/matching.py",
    "app/api/v1/endpoints/staff_matching/performance.py",
    "app/api/v1/endpoints/staff_matching/profiles.py",
    "app/api/v1/endpoints/staff_matching/staffing_needs.py",
    "app/api/v1/endpoints/staff_matching/tags.py",
    "app/api/v1/endpoints/stage_templates.py",
    "app/api/v1/endpoints/standard_costs/crud.py",
    "app/api/v1/endpoints/standard_costs/history.py",
    "app/api/v1/endpoints/standard_costs/project_integration.py",
    "app/api/v1/endpoints/task_center/batch_attributes.py",
    "app/api/v1/endpoints/task_center/comments.py",
    "app/api/v1/endpoints/task_center/complete.py",
    "app/api/v1/endpoints/task_center/create.py",
    "app/api/v1/endpoints/task_center/detail.py",
    "app/api/v1/endpoints/task_center/reject.py",
    "app/api/v1/endpoints/task_center/transfer.py",
    "app/api/v1/endpoints/technical_review/checklists.py",
    "app/api/v1/endpoints/technical_review/issues.py",
    "app/api/v1/endpoints/technical_review/materials.py",
    "app/api/v1/endpoints/technical_review/participants.py",
    "app/api/v1/endpoints/technical_review/reviews.py",
    "app/api/v1/endpoints/technical_spec/match.py",
    "app/api/v1/endpoints/technical_spec/requirements.py",
    "app/api/v1/endpoints/timesheet/records.py",
    "app/api/v1/endpoints/users/crud_refactored.py",
    "app/api/v1/endpoints/users/sync.py",
    "app/api/v1/endpoints/users/time_allocation.py",
    "app/api/v1/endpoints/users/utils.py",
]


def fix_db_helpers_import(content: str, use_get_or_404: bool, use_save_obj: bool) -> tuple[str, bool]:
    """
    智能处理 db_helpers 导入:
    - 如果没有 db_helpers 导入，添加完整 import 行
    - 如果有但缺少某个符号，更新导入行
    返回 (新内容, 是否有变更)
    """
    existing = re.search(r'^from app\.utils\.db_helpers import (.+)$', content, re.MULTILINE)
    
    if not existing:
        # 完全没有，如果有实际使用才添加
        if not use_get_or_404 and not use_save_obj:
            return content, False
        # 添加完整导入
        content = insert_import_line(content, "from app.utils.db_helpers import get_or_404, save_obj, delete_obj")
        return content, True
    
    # 已有导入，检查是否需要补充
    current_imports_str = existing.group(1)
    current_imports = {s.strip() for s in current_imports_str.split(',')}
    
    needed = set()
    if use_get_or_404:
        needed.add('get_or_404')
    if use_save_obj:
        needed.add('save_obj')
    
    missing = needed - current_imports
    if not missing:
        return content, False
    
    # 更新现有导入行
    all_symbols = sorted(current_imports | missing)
    new_import_line = f"from app.utils.db_helpers import {', '.join(all_symbols)}"
    content = re.sub(r'^from app\.utils\.db_helpers import .+$', new_import_line, content, flags=re.MULTILINE)
    return content, True


def insert_import_line(content: str, import_line: str) -> str:
    """在合适位置插入import行"""
    lines = content.split('\n')
    
    # 找最后一个 'from app.' 导入行
    last_app_import_idx = -1
    last_import_idx = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('from app.') or stripped.startswith('import app.'):
            last_app_import_idx = i
        if stripped.startswith('from ') or stripped.startswith('import '):
            last_import_idx = i
    
    insert_after = last_app_import_idx if last_app_import_idx >= 0 else last_import_idx
    
    if insert_after < 0:
        # 找到 docstring 结束位置
        insert_after = 0
        for i, line in enumerate(lines[:20]):
            stripped = line.strip()
            if stripped.startswith('"""') and i > 0:
                insert_after = i
                break
    
    lines.insert(insert_after + 1, import_line)
    return '\n'.join(lines)


def apply_rule1_get_or_404(content: str) -> tuple[str, int]:
    """
    规则1: 替换 query + 404 模式 (简单字符串detail)
    
    obj = db.query(Model).filter(Model.id == var).first()
    if not obj:
        raise HTTPException(status_code=404, detail="xxx")
    ->
    obj = get_or_404(db, Model, var, "xxx")
    
    注意: 只替换 detail 为简单字符串（不含f-string、变量等）
    """
    count = 0
    
    # 支持单行查询 + 2行if块（精确匹配简单字符串detail）
    pattern = re.compile(
        r'^(?P<indent>[ \t]*)(?P<var>\w+)\s*=\s*db\.query\((?P<model>\w+)\)\.filter\('
        r'(?P=model)\.id\s*==\s*(?P<id_val>\w+)\)\.first\(\)\s*\n'
        r'(?P=indent)if\s+not\s+(?P=var)\s*:\s*\n'
        r'(?P=indent)[ \t]+raise\s+HTTPException\s*\('
        r'(?:\s*status_code\s*=\s*404\s*,\s*detail\s*=\s*(?P<detail>["\'][^"\']*["\'])\s*'
        r'|\s*detail\s*=\s*(?P<detail2>["\'][^"\']*["\'])\s*,\s*status_code\s*=\s*404\s*)'
        r'\)',
        re.MULTILINE
    )
    
    def replacer(m):
        nonlocal count
        indent = m.group('indent')
        var = m.group('var')
        model = m.group('model')
        id_val = m.group('id_val')
        detail = m.group('detail') or m.group('detail2')
        count += 1
        return f'{indent}{var} = get_or_404(db, {model}, {id_val}, {detail})'
    
    content = pattern.sub(replacer, content)
    return content, count


def apply_rule2_save_obj(content: str) -> tuple[str, int]:
    """
    规则2: 替换连续的 db.add + db.commit + db.refresh + return
    
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
    ->
    return save_obj(db, obj)
    """
    count = 0
    
    pattern = re.compile(
        r'^(?P<indent>[ \t]*)db\.add\((?P<obj>\w+)\)\s*\n'
        r'(?P=indent)db\.commit\(\)\s*\n'
        r'(?P=indent)db\.refresh\((?P=obj)\)\s*\n'
        r'(?P=indent)return\s+(?P=obj)\b',
        re.MULTILINE
    )
    
    def replacer(m):
        nonlocal count
        indent = m.group('indent')
        obj = m.group('obj')
        count += 1
        return f'{indent}return save_obj(db, {obj})'
    
    content = pattern.sub(replacer, content)
    return content, count


def process_file(rel_path: str) -> dict:
    """处理单个文件"""
    filepath = BASE_DIR / rel_path
    result = {
        'file': rel_path,
        'status': 'no_change',
        'rule1_count': 0,
        'rule2_count': 0,
        'import_changed': False,
        'error': None,
    }
    
    if not filepath.exists():
        result['status'] = 'not_found'
        result['error'] = 'File not found'
        return result
    
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    # 检查原始语法
    try:
        ast.parse(original)
    except SyntaxError as e:
        result['status'] = 'error'
        result['error'] = f'Original syntax error: {e}'
        return result
    
    content = original
    
    # 应用规则1 (query + 404)
    content, r1_count = apply_rule1_get_or_404(content)
    result['rule1_count'] = r1_count
    
    # 应用规则2 (db.add + commit + refresh + return)
    content, r2_count = apply_rule2_save_obj(content)
    result['rule2_count'] = r2_count
    
    # 处理导入 (基于实际使用情况)
    use_get_or_404 = r1_count > 0 or 'get_or_404(' in content
    use_save_obj = r2_count > 0 or 'save_obj(' in content
    
    content, import_changed = fix_db_helpers_import(content, use_get_or_404, use_save_obj)
    result['import_changed'] = import_changed
    
    total_changes = r1_count + r2_count
    
    # 如果内容没变化
    if content == original:
        result['status'] = 'no_change'
        return result
    
    # 验证新内容语法
    try:
        ast.parse(content)
    except SyntaxError as e:
        result['status'] = 'error'
        result['error'] = f'New content syntax error: {e}'
        # 不写入，保留原文件
        return result
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    result['status'] = 'modified'
    return result


def main():
    print("=" * 60)
    print("E组代码去重 - 开始处理")
    print("=" * 60)
    
    results = []
    modified_count = 0
    no_change_count = 0
    error_count = 0
    not_found_count = 0
    
    total_r1 = 0
    total_r2 = 0
    
    for rel_path in FILES:
        r = process_file(rel_path)
        results.append(r)
        
        status_icon = {
            'modified': '✅',
            'no_change': '⏭',
            'error': '❌',
            'not_found': '🔍',
        }.get(r['status'], '?')
        
        if r['status'] == 'modified':
            modified_count += 1
            total_r1 += r['rule1_count']
            total_r2 += r['rule2_count']
            print(f"{status_icon} {rel_path}")
            if r['rule1_count']:
                print(f"   规则1(get_or_404): {r['rule1_count']} 处")
            if r['rule2_count']:
                print(f"   规则2(save_obj):   {r['rule2_count']} 处")
            if r['import_changed']:
                print(f"   import: 已更新")
        elif r['status'] == 'no_change':
            no_change_count += 1
            print(f"{status_icon} {rel_path}")
        elif r['status'] == 'error':
            error_count += 1
            print(f"{status_icon} {rel_path}: {r['error']}")
        elif r['status'] == 'not_found':
            not_found_count += 1
            print(f"{status_icon} {rel_path}: 文件不存在")
    
    print("\n" + "=" * 60)
    print(f"处理完成:")
    print(f"  ✅ 修改: {modified_count} 个文件")
    print(f"  ⏭ 无变更: {no_change_count} 个文件")
    print(f"  ❌ 错误: {error_count} 个文件")
    print(f"  🔍 未找到: {not_found_count} 个文件")
    print(f"\n规则统计:")
    print(f"  规则1(get_or_404): 共 {total_r1} 处替换")
    print(f"  规则2(save_obj):   共 {total_r2} 处替换")
    
    return results, modified_count, total_r1, total_r2


if __name__ == "__main__":
    results, modified_count, total_r1, total_r2 = main()
    
    # 保存结果用于报告
    import json
    with open('/tmp/dedup_e_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'results': results,
            'modified_count': modified_count,
            'total_r1': total_r1,
            'total_r2': total_r2,
        }, f, ensure_ascii=False, indent=2)
