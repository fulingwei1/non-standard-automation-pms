#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理重复和错误的部门数据

功能：
1. 识别同一父部门下的重复部门名称
2. 识别包含父部门名称的冗余部门（如"营销中心-商务部"）
3. 识别明显的错误数据（如"海尔治县"）
4. 提供清理建议和自动清理功能
"""

import os
import sqlite3
import sys
from typing import Dict, List

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)



def find_duplicate_departments(db_path: str) -> List[Dict]:
    """查找重复的部门"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查找同一父部门下名称相同的部门
    cursor.execute("""
        SELECT parent_id, dept_name, GROUP_CONCAT(id || ':' || dept_code, ', ') as dept_list
        FROM departments
        WHERE is_active = 1
        GROUP BY parent_id, dept_name
        HAVING COUNT(*) > 1
    """)

    duplicates = []
    for row in cursor.fetchall():
        parent_id, dept_name, dept_list = row
        dept_items = [item.split(':') for item in dept_list.split(', ')]
        duplicates.append({
            'type': 'duplicate_name',
            'parent_id': parent_id,
            'dept_name': dept_name,
            'departments': [{'id': int(item[0]), 'code': item[1]} for item in dept_items]
        })

    conn.close()
    return duplicates


def find_redundant_departments(db_path: str) -> List[Dict]:
    """查找包含父部门名称的冗余部门"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有有父部门的部门
    cursor.execute("""
        SELECT d.id, d.dept_code, d.dept_name, d.parent_id, p.dept_name as parent_name
        FROM departments d
        JOIN departments p ON d.parent_id = p.id
        WHERE d.is_active = 1 AND p.is_active = 1
    """)

    redundant = []
    for row in cursor.fetchall():
        dept_id, dept_code, dept_name, parent_id, parent_name = row
        # 检查部门名称是否包含父部门名称
        if parent_name in dept_name and dept_name != parent_name:
            # 提取建议的部门名称（移除父部门名称）
            suggested_name = dept_name.replace(parent_name + '-', '').replace(parent_name, '').strip()
            redundant.append({
                'type': 'redundant_name',
                'id': dept_id,
                'code': dept_code,
                'dept_name': dept_name,
                'parent_id': parent_id,
                'parent_name': parent_name,
                'suggested_name': suggested_name
            })

    conn.close()
    return redundant


def find_error_departments(db_path: str) -> List[Dict]:
    """查找明显的错误数据"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 常见的错误数据模式
    error_patterns = [
        ('海尔治县', '疑似地名，非部门名称'),
        ('测试', '测试数据'),
        ('test', '测试数据'),
        ('示例', '示例数据'),
    ]

    errors = []
    for pattern, reason in error_patterns:
        cursor.execute("""
            SELECT id, dept_code, dept_name, parent_id
            FROM departments
            WHERE dept_name LIKE ? AND is_active = 1
        """, (f'%{pattern}%',))

        for row in cursor.fetchall():
            dept_id, dept_code, dept_name, parent_id = row
            errors.append({
                'type': 'error_data',
                'id': dept_id,
                'code': dept_code,
                'dept_name': dept_name,
                'parent_id': parent_id,
                'reason': reason
            })

    conn.close()
    return errors


def get_parent_path(db_path: str, dept_id: int) -> str:
    """获取部门的完整路径"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    path = []
    current_id = dept_id

    while current_id:
        cursor.execute("SELECT dept_name, parent_id FROM departments WHERE id = ?", (current_id,))
        row = cursor.fetchone()
        if not row:
            break
        dept_name, parent_id = row
        path.insert(0, dept_name)
        current_id = parent_id

    conn.close()
    return ' > '.join(path) if path else ''


def print_report(duplicates: List[Dict], redundant: List[Dict], errors: List[Dict], db_path: str):
    """打印清理报告"""
    print("=" * 80)
    print("部门数据清理报告")
    print("=" * 80)

    if not duplicates and not redundant and not errors:
        print("\n✅ 未发现需要清理的数据")
        return

    if duplicates:
        print(f"\n【1. 重复部门】发现 {len(duplicates)} 组重复的部门名称：")
        for dup in duplicates:
            parent_name = "根部门" if dup['parent_id'] is None else get_parent_path(db_path, dup['parent_id'])
            print(f"\n  父部门: {parent_name}")
            print(f"  部门名称: {dup['dept_name']}")
            print(f"  重复的部门:")
            for dept in dup['departments']:
                print(f"    - {dept['code']} (ID: {dept['id']})")

    if redundant:
        print(f"\n【2. 冗余命名】发现 {len(redundant)} 个包含父部门名称的部门：")
        for red in redundant:
            path = get_parent_path(db_path, red['id'])
            print(f"\n  部门路径: {path}")
            print(f"  当前名称: {red['dept_name']}")
            print(f"  建议名称: {red['suggested_name']}")
            print(f"  部门编码: {red['code']} (ID: {red['id']})")

    if errors:
        print(f"\n【3. 错误数据】发现 {len(errors)} 个疑似错误的数据：")
        for err in errors:
            path = get_parent_path(db_path, err['id'])
            print(f"\n  部门路径: {path}")
            print(f"  部门名称: {err['dept_name']}")
            print(f"  错误原因: {err['reason']}")
            print(f"  部门编码: {err['code']} (ID: {err['id']})")

    print("\n" + "=" * 80)


def cleanup_redundant_departments(db_path: str, redundant: List[Dict], dry_run: bool = True):
    """清理冗余命名的部门"""
    if not redundant:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n{'[模拟运行]' if dry_run else '[实际执行]'} 清理冗余命名部门：")

    for red in redundant:
        suggested_name = red['suggested_name']
        if not suggested_name:
            print(f"  跳过 {red['code']} ({red['dept_name']})：无法生成建议名称")
            continue

        if dry_run:
            print(f"  将重命名: {red['dept_name']} -> {suggested_name} ({red['code']})")
        else:
            cursor.execute("""
                UPDATE departments
                SET dept_name = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (suggested_name, red['id']))
            print(f"  ✓ 已重命名: {red['dept_name']} -> {suggested_name} ({red['code']})")

    if not dry_run:
        conn.commit()

    conn.close()


def cleanup_error_departments(db_path: str, errors: List[Dict], dry_run: bool = True):
    """清理错误数据（标记为不活跃）"""
    if not errors:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n{'[模拟运行]' if dry_run else '[实际执行]'} 清理错误数据：")

    for err in errors:
        if dry_run:
            print(f"  将禁用: {err['dept_name']} ({err['code']}) - {err['reason']}")
        else:
            cursor.execute("""
                UPDATE departments
                SET is_active = 0, updated_at = datetime('now')
                WHERE id = ?
            """, (err['id'],))
            print(f"  ✓ 已禁用: {err['dept_name']} ({err['code']}) - {err['reason']}")

    if not dry_run:
        conn.commit()

    conn.close()


def main():
    """主函数"""
    db_path = os.path.join(project_dir, 'data', 'app.db')

    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在: {db_path}")
        return

    print("正在分析部门数据...")

    # 查找问题数据
    duplicates = find_duplicate_departments(db_path)
    redundant = find_redundant_departments(db_path)
    errors = find_error_departments(db_path)

    # 打印报告
    print_report(duplicates, redundant, errors, db_path)

    if not redundant and not errors:
        print("\n无需执行清理操作")
        return

    # 询问是否执行清理
    print("\n" + "=" * 80)
    print("清理选项：")
    print("1. 仅查看报告（不执行清理）")
    print("2. 模拟运行（查看将执行的操作）")
    print("3. 执行清理（重命名冗余部门，禁用错误数据）")
    print("=" * 80)

    choice = input("\n请选择操作 [1/2/3] (默认: 1): ").strip() or "1"

    if choice == "1":
        print("\n已取消清理操作")
    elif choice == "2":
        cleanup_redundant_departments(db_path, redundant, dry_run=True)
        cleanup_error_departments(db_path, errors, dry_run=True)
        print("\n模拟运行完成，如需实际执行，请选择选项 3")
    elif choice == "3":
        confirm = input("\n确认执行清理操作？这将修改数据库 [y/N]: ").strip().lower()
        if confirm == 'y':
            cleanup_redundant_departments(db_path, redundant, dry_run=False)
            cleanup_error_departments(db_path, errors, dry_run=False)
            print("\n✅ 清理完成！")
        else:
            print("\n已取消清理操作")
    else:
        print("\n无效的选择")


if __name__ == '__main__':
    main()
