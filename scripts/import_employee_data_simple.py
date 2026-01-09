# -*- coding: utf-8 -*-
"""
从 Excel 导入员工档案数据（简化版，直接SQL操作）
数据源：data/ATE-人事档案系统.xlsx
"""

import os
import sys
from datetime import datetime
import sqlite3

import pandas as pd


def clean_name(name):
    """清理姓名中的特殊字符"""
    if pd.isna(name):
        return None
    # 去除换行符和空白
    return str(name).replace('\n', '').strip()


def clean_phone(phone):
    """清理电话号码"""
    if pd.isna(phone):
        return None
    # 转为字符串，去除科学计数法
    phone_str = str(phone)
    if 'e' in phone_str.lower() or '.' in phone_str:
        try:
            phone_str = str(int(float(phone)))
        except:
            pass
    return phone_str.strip()


def get_department_name(row):
    """组合部门名称"""
    parts = []
    for col in ['一级部门', '二级部门', '三级部门']:
        val = row.get(col)
        if pd.notna(val) and str(val).strip() not in ['/', 'NaN', '']:
            parts.append(str(val).strip())
    return '-'.join(parts) if parts else None


def is_active_employee(status):
    """判断是否在职"""
    if pd.isna(status):
        return 1  # 默认在职
    status_str = str(status).strip()
    # 离职状态
    if status_str in ['离职', '已离职']:
        return 0
    return 1


def import_employees():
    """导入员工数据"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    excel_path = os.path.join(project_dir, 'data', 'ATE-人事档案系统.xlsx')
    db_path = os.path.join(project_dir, 'data', 'app.db')

    if not os.path.exists(excel_path):
        print(f"错误：找不到文件 {excel_path}")
        return

    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在 {db_path}")
        return

    print(f"读取 Excel 文件: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name='员工信息表')
    print(f"共 {len(df)} 条记录")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 获取现有员工
        cursor.execute("SELECT employee_code, name, department FROM employees")
        existing = {(row[1], row[2]): row[0] for row in cursor.fetchall()}
        existing_codes = set(row[0] for row in cursor.execute("SELECT employee_code FROM employees"))

        # 获取管理员用户ID
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_row = cursor.fetchone()
        evaluator_id = admin_row[0] if admin_row else 1

        # 获取标签字典
        cursor.execute("SELECT id, tag_name FROM hr_tag_dict WHERE is_active = 1")
        tag_dict = {row[1]: row[0] for row in cursor.fetchall()}

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        today = datetime.now().strftime('%Y-%m-%d')

        imported_count = 0
        updated_count = 0
        skipped_count = 0

        for idx, row in df.iterrows():
            name = clean_name(row.get('姓名'))
            if not name:
                skipped_count += 1
                continue

            department = get_department_name(row)
            position = str(row.get('职务', '')).strip() if pd.notna(row.get('职务')) else None
            phone = clean_phone(row.get('联系方式'))
            is_active = is_active_employee(row.get('在职离职状态'))

            # 检查是否已存在
            key = (name, department)
            if key in existing:
                # 更新现有员工
                cursor.execute("""
                    UPDATE employees SET
                        phone = COALESCE(?, phone),
                        role = COALESCE(?, role),
                        is_active = ?,
                        updated_at = ?
                    WHERE name = ? AND (department = ? OR (department IS NULL AND ? IS NULL))
                """, (phone, position, is_active, now, name, department, department))
                updated_count += 1
                employee_code = existing[key]
                cursor.execute("SELECT id FROM employees WHERE employee_code = ?", (employee_code,))
                employee_id = cursor.fetchone()[0]
            else:
                # 生成新员工编码
                code_idx = idx + 1
                employee_code = f"EMP{code_idx:04d}"
                while employee_code in existing_codes:
                    code_idx += 1
                    employee_code = f"EMP{code_idx:04d}"
                existing_codes.add(employee_code)

                # 插入新员工
                cursor.execute("""
                    INSERT INTO employees (employee_code, name, department, role, phone, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (employee_code, name, department, position, phone, is_active, now, now))
                employee_id = cursor.lastrowid
                imported_count += 1

            # 创建员工档案（如果不存在）
            cursor.execute("SELECT id FROM hr_employee_profile WHERE employee_id = ?", (employee_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO hr_employee_profile
                    (employee_id, skill_tags, domain_tags, attitude_tags, character_tags, special_tags,
                     current_workload_pct, total_projects, profile_updated_at, created_at, updated_at)
                    VALUES (?, '[]', '[]', '[]', '[]', '[]', 0, 0, ?, ?, ?)
                """, (employee_id, now, now, now))

            # 根据职位自动添加技能标签评估
            if position and is_active:
                skill_mappings = {
                    'PLC': ['PLC编程'],
                    '测试': ['ICT测试', 'FCT测试'],
                    '机械': ['机械设计', '3D建模'],
                    '电气': ['电气原理图'],
                    '视觉': ['视觉系统'],
                    '客服': ['故障排除', '现场经验'],
                    '装配': ['装配调试'],
                    'HMI': ['HMI开发'],
                    '硬件': ['电气原理图'],
                    '软件': ['PLC编程', 'HMI开发'],
                }

                matched_tags = set()
                for keyword, tag_names in skill_mappings.items():
                    if keyword in (position or ''):
                        for tag_name in tag_names:
                            if tag_name in tag_dict:
                                matched_tags.add(tag_name)

                # 添加标签评估
                for tag_name in matched_tags:
                    tag_id = tag_dict.get(tag_name)
                    if tag_id:
                        cursor.execute("""
                            SELECT id FROM hr_employee_tag_evaluation
                            WHERE employee_id = ? AND tag_id = ?
                        """, (employee_id, tag_id))
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO hr_employee_tag_evaluation
                                (employee_id, tag_id, score, evidence, evaluator_id, evaluate_date, is_valid, created_at, updated_at)
                                VALUES (?, ?, 3, ?, ?, ?, 1, ?, ?)
                            """, (employee_id, tag_id, f'根据职位 "{position}" 自动匹配', evaluator_id, today, now, now))

            if (idx + 1) % 100 == 0:
                print(f"已处理 {idx + 1} 条记录...")
                conn.commit()

        conn.commit()

        print(f"\n导入完成:")
        print(f"  - 新增员工: {imported_count}")
        print(f"  - 更新员工: {updated_count}")
        print(f"  - 跳过记录: {skipped_count}")

        # 统计数据
        cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM employees WHERE is_active = 1")
        active_employees = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM hr_employee_profile")
        total_profiles = cursor.fetchone()[0]

        print(f"\n数据库统计:")
        print(f"  - 员工总数: {total_employees}")
        print(f"  - 在职员工: {active_employees}")
        print(f"  - 员工档案: {total_profiles}")

    except Exception as e:
        conn.rollback()
        print(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def import_departments():
    """从员工数据中提取并导入部门结构"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    excel_path = os.path.join(project_dir, 'data', 'ATE-人事档案系统.xlsx')
    db_path = os.path.join(project_dir, 'data', 'app.db')

    df = pd.read_excel(excel_path, sheet_name='员工信息表')

    # 提取所有部门组合
    dept_hierarchy = {}
    for idx, row in df.iterrows():
        level1 = str(row.get('一级部门', '')).strip() if pd.notna(row.get('一级部门')) else None
        level2 = str(row.get('二级部门', '')).strip() if pd.notna(row.get('二级部门')) else None
        level3 = str(row.get('三级部门', '')).strip() if pd.notna(row.get('三级部门')) else None

        if level1 and level1 not in ['/', 'NaN', '']:
            if level1 not in dept_hierarchy:
                dept_hierarchy[level1] = {}

            if level2 and level2 not in ['/', 'NaN', '']:
                if level2 not in dept_hierarchy[level1]:
                    dept_hierarchy[level1][level2] = set()

                if level3 and level3 not in ['/', 'NaN', '']:
                    dept_hierarchy[level1][level2].add(level3)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        dept_code_counter = 1

        for level1_name, level2_dict in dept_hierarchy.items():
            # 检查一级部门是否存在
            cursor.execute("""
                SELECT id FROM departments WHERE dept_name = ? AND level = 1
            """, (level1_name,))
            row = cursor.fetchone()

            if row:
                level1_id = row[0]
            else:
                cursor.execute("""
                    INSERT INTO departments (dept_code, dept_name, level, is_active, created_at, updated_at)
                    VALUES (?, ?, 1, 1, ?, ?)
                """, (f"D{dept_code_counter:03d}", level1_name, now, now))
                level1_id = cursor.lastrowid
                dept_code_counter += 1

            for level2_name, level3_set in level2_dict.items():
                # 检查二级部门是否存在
                cursor.execute("""
                    SELECT id FROM departments WHERE dept_name = ? AND parent_id = ?
                """, (level2_name, level1_id))
                row = cursor.fetchone()

                if row:
                    level2_id = row[0]
                else:
                    cursor.execute("""
                        INSERT INTO departments (dept_code, dept_name, parent_id, level, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, 2, 1, ?, ?)
                    """, (f"D{dept_code_counter:03d}", level2_name, level1_id, now, now))
                    level2_id = cursor.lastrowid
                    dept_code_counter += 1

                for level3_name in level3_set:
                    # 检查三级部门是否存在
                    cursor.execute("""
                        SELECT id FROM departments WHERE dept_name = ? AND parent_id = ?
                    """, (level3_name, level2_id))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO departments (dept_code, dept_name, parent_id, level, is_active, created_at, updated_at)
                            VALUES (?, ?, ?, 3, 1, ?, ?)
                        """, (f"D{dept_code_counter:03d}", level3_name, level2_id, now, now))
                        dept_code_counter += 1

        conn.commit()

        # 统计
        cursor.execute("SELECT COUNT(*) FROM departments")
        total_depts = cursor.fetchone()[0]
        print(f"部门导入完成，共 {total_depts} 个部门")

    except Exception as e:
        conn.rollback()
        print(f"部门导入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 50)
    print("开始导入员工档案数据")
    print("=" * 50)

    print("\n[1/2] 导入部门结构...")
    import_departments()

    print("\n[2/2] 导入员工数据...")
    import_employees()

    print("\n" + "=" * 50)
    print("数据导入完成！")
    print("=" * 50)
