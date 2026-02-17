#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B组代码去重脚本 v2
- 添加 db_helpers import（安全地插入在顶层 import 块末尾）
- 替换查询+404模式
- 替换 db.add+commit+refresh+return 模式
"""

import re
import ast
import sys
from pathlib import Path

IMPORT_LINE = "from app.utils.db_helpers import get_or_404, save_obj, delete_obj"

FILES = [
    "app/api/v1/endpoints/audits.py",
    "app/api/v1/endpoints/backup.py",
    "app/api/v1/endpoints/bom/bom_detail.py",
    "app/api/v1/endpoints/bom/bom_items.py",
    "app/api/v1/endpoints/bom/bom_versions.py",
    "app/api/v1/endpoints/bonus/allocation_sheets/crud.py",
    "app/api/v1/endpoints/bonus/allocation_sheets/download.py",
    "app/api/v1/endpoints/bonus/allocation_sheets/operations.py",
    "app/api/v1/endpoints/bonus/allocation_sheets/rows.py",
    "app/api/v1/endpoints/bonus/calculation.py",
    "app/api/v1/endpoints/bonus/payment.py",
    "app/api/v1/endpoints/bonus/rules.py",
    "app/api/v1/endpoints/bonus/sales_calc.py",
    "app/api/v1/endpoints/bonus/team.py",
    "app/api/v1/endpoints/budget/allocation_rules.py",
    "app/api/v1/endpoints/budget/budgets.py",
    "app/api/v1/endpoints/budget/items.py",
    "app/api/v1/endpoints/business_support/bidding.py",
    "app/api/v1/endpoints/business_support/contract_review.py",
    "app/api/v1/endpoints/business_support/contract_seal.py",
    "app/api/v1/endpoints/business_support/payment_reminders.py",
    "app/api/v1/endpoints/business_support_orders/customer_registrations.py",
    "app/api/v1/endpoints/business_support_orders/delivery_orders/crud.py",
    "app/api/v1/endpoints/business_support_orders/invoice_requests.py",
    "app/api/v1/endpoints/business_support_orders/reconciliations.py",
    "app/api/v1/endpoints/business_support_orders/sales_orders/crud.py",
    "app/api/v1/endpoints/business_support_orders/sales_orders/operations.py",
    "app/api/v1/endpoints/business_support_orders/sales_reports.py",
    "app/api/v1/endpoints/business_support_orders/tracking_crud.py",
    "app/api/v1/endpoints/business_support_orders/tracking_operations.py",
    "app/api/v1/endpoints/change_impact.py",
    "app/api/v1/endpoints/culture_wall/contents.py",
    "app/api/v1/endpoints/culture_wall/goals.py",
    "app/api/v1/endpoints/customers/view360.py",
    "app/api/v1/endpoints/dashboard/cost_dashboard.py",
    "app/api/v1/endpoints/dashboard_unified.py",
    "app/api/v1/endpoints/departments/__init__.py",
    "app/api/v1/endpoints/documents/crud_refactored.py",
    "app/api/v1/endpoints/documents/operations.py",
    "app/api/v1/endpoints/ecn/approval.py",
    "app/api/v1/endpoints/ecn/core.py",
    "app/api/v1/endpoints/ecn/evaluations.py",
    "app/api/v1/endpoints/ecn/execution.py",
    "app/api/v1/endpoints/ecn/impacts.py",
    "app/api/v1/endpoints/ecn/integration.py",
]


def find_top_level_import_end(content: str) -> int:
    """
    使用 AST 找到顶层 import 块的最后一行（行号从0起），
    返回插入点（在该行之后插入）。
    使用 tokenize 来跳过注释和字符串。
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return -1
    
    # 找到所有顶层 import 语句的行号（end_lineno，1-indexed）
    last_import_line = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # 只考虑顶层（col_offset == 0 的）
            if node.col_offset == 0:
                last_import_line = max(last_import_line, node.end_lineno)
    
    return last_import_line  # 1-indexed


def add_import_if_missing(content: str) -> tuple:
    """安全地添加 db_helpers import（如果没有的话）"""
    if IMPORT_LINE in content:
        return content, False
    
    last_import_line = find_top_level_import_end(content)
    
    if last_import_line <= 0:
        # fallback: just prepend after first non-empty line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#'):
                lines.insert(i + 1, IMPORT_LINE)
                return '\n'.join(lines), True
        return content + '\n' + IMPORT_LINE + '\n', True
    
    lines = content.split('\n')
    # Insert after last_import_line (0-indexed = last_import_line - 1)
    insert_pos = last_import_line  # insert AFTER line at index last_import_line-1
    lines.insert(insert_pos, IMPORT_LINE)
    return '\n'.join(lines), True


def replace_query_404_pattern(content: str) -> tuple:
    """
    替换模式：
    var = db.query(Model).filter(Model.id == some_id).first()
    if not var:
        raise HTTPException(status_code=404, detail="xxx")
    
    ->
    
    var = get_or_404(db, Model, some_id, "xxx")
    """
    count = 0
    
    pattern = re.compile(
        r'^( *)'                              # Group 1: indent
        r'(\w+) = '                           # Group 2: variable name
        r'db\.query\((\w+)\)'                 # Group 3: Model
        r'\.filter\(\3\.(\w+) == (\w+)\)'     # Group 4: field, Group 5: id_var
        r'\.first\(\)\n'
        r'\1if not \2:\n'
        r'\1    raise HTTPException\(status_code=404, detail="([^"]+)"\)',
        re.MULTILINE
    )
    
    def replace_match(m):
        nonlocal count
        indent = m.group(1)
        var_name = m.group(2)
        model_name = m.group(3)
        field_name = m.group(4)
        id_var = m.group(5)
        detail = m.group(6)
        
        # Only replace when field is "id" (standard pattern)
        if field_name == "id":
            count += 1
            return f'{indent}{var_name} = get_or_404(db, {model_name}, {id_var}, "{detail}")'
        else:
            return m.group(0)
    
    content = pattern.sub(replace_match, content)
    return content, count


def replace_add_commit_refresh_return(content: str) -> tuple:
    """
    替换模式：
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    
    ->
    
        return save_obj(db, obj)
    """
    count = 0
    
    pattern = re.compile(
        r'^( *)db\.add\((\w+)\)\n'
        r'\1db\.commit\(\)\n'
        r'\1db\.refresh\(\2\)\n'
        r'\1return \2\b',
        re.MULTILINE
    )
    
    def replace_match(m):
        nonlocal count
        indent = m.group(1)
        obj_name = m.group(2)
        count += 1
        return f'{indent}return save_obj(db, {obj_name})'
    
    content = pattern.sub(replace_match, content)
    return content, count


def process_file(filepath: str, base_dir: Path) -> dict:
    """处理单个文件"""
    full_path = base_dir / filepath
    
    if not full_path.exists():
        return {"file": filepath, "status": "skipped", "reason": "file not found"}
    
    original = full_path.read_text(encoding='utf-8')
    content = original
    
    # Step 1: Replace patterns
    content, pattern1_count = replace_query_404_pattern(content)
    content, pattern2_count = replace_add_commit_refresh_return(content)
    
    import_added = False
    
    # Step 2: Add import if file uses db_helpers functions
    uses_get_or_404 = 'get_or_404(' in content
    uses_save_obj = 'save_obj(' in content
    uses_delete_obj = 'delete_obj(' in content
    
    if uses_get_or_404 or uses_save_obj or uses_delete_obj:
        content, import_added = add_import_if_missing(content)
    
    if content == original:
        return {
            "file": filepath,
            "status": "unchanged",
            "pattern1_replacements": 0,
            "pattern2_replacements": 0,
            "import_added": False
        }
    
    # Write back
    full_path.write_text(content, encoding='utf-8')
    
    return {
        "file": filepath,
        "status": "modified",
        "pattern1_replacements": pattern1_count,
        "pattern2_replacements": pattern2_count,
        "import_added": import_added
    }


def verify_syntax(filepath: str, base_dir: Path) -> tuple:
    """验证Python语法，返回 (ok, error_msg)"""
    full_path = base_dir / filepath
    try:
        content = full_path.read_text(encoding='utf-8')
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"line {e.lineno}: {e.msg}"


def main():
    base_dir = Path("/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms")
    
    results = []
    syntax_errors = []
    
    for filepath in FILES:
        result = process_file(filepath, base_dir)
        results.append(result)
        
        # Verify syntax for modified files
        if result["status"] == "modified":
            ok, err = verify_syntax(filepath, base_dir)
            if not ok:
                syntax_errors.append((filepath, err))
                print(f"SYNTAX ERROR in {filepath}: {err}", file=sys.stderr)
    
    # Print summary
    print("\n=== B组代码去重处理结果 ===\n")
    
    modified = [r for r in results if r["status"] == "modified"]
    unchanged = [r for r in results if r["status"] == "unchanged"]
    skipped = [r for r in results if r["status"] == "skipped"]
    
    print(f"总文件数: {len(FILES)}")
    print(f"已修改: {len(modified)}")
    print(f"未变更: {len(unchanged)}")
    print(f"已跳过: {len(skipped)}")
    
    if syntax_errors:
        print(f"\n❌ 语法错误文件: {len(syntax_errors)}")
        for f, err in syntax_errors:
            print(f"  - {f}: {err}")
    else:
        print("\n✅ 所有修改文件语法验证通过")
    
    print("\n=== 修改详情 ===")
    total_p1 = 0
    total_p2 = 0
    
    for r in results:
        if r["status"] == "modified":
            p1 = r.get("pattern1_replacements", 0)
            p2 = r.get("pattern2_replacements", 0)
            total_p1 += p1
            total_p2 += p2
            parts = []
            if p1:
                parts.append(f"get_or_404×{p1}")
            if p2:
                parts.append(f"save_obj×{p2}")
            if r.get("import_added"):
                parts.append("+import")
            print(f"  ✓ {r['file']}" + (f" [{', '.join(parts)}]" if parts else ""))
    
    print(f"\n汇总:")
    print(f"  get_or_404 替换总数: {total_p1}")
    print(f"  save_obj 替换总数: {total_p2}")
    
    if syntax_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
