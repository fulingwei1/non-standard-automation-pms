# -*- coding: utf-8 -*-
"""
从 Excel 导入员工档案数据
数据源：data/ATE-人事档案系统.xlsx
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from app.models.base import SessionLocal
from app.models.organization import Department, Employee
from app.models.staff_matching import (
    HrEmployeeProfile,
    HrEmployeeTagEvaluation,
    HrTagDict,
)
from app.models.user import User


def clean_name(name):
    """清理姓名中的特殊字符"""
    if pd.isna(name):
        return None
    # 去除换行符和空白
    return str(name).replace("\n", "").strip()


def clean_phone(phone):
    """清理电话号码"""
    if pd.isna(phone):
        return None
    # 转为字符串，去除科学计数法
    phone_str = str(phone)
    if "e" in phone_str.lower() or "." in phone_str:
        try:
            phone_str = str(int(float(phone)))
        except (ValueError, TypeError, OverflowError):
            pass
    return phone_str.strip()


def parse_entry_date(date_val):
    """解析入职日期"""
    if pd.isna(date_val):
        return None
    date_str = str(date_val).strip()

    # 尝试多种格式
    formats = ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日", "%Y.%m.%d", "%Y%m%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.split()[0], fmt).date()
        except ValueError:
            continue
    return None


def get_department_name(row):
    """组合部门名称"""
    parts = []
    for col in ["一级部门", "二级部门", "三级部门"]:
        val = row.get(col)
        if pd.notna(val) and str(val).strip() not in ["/", "NaN", ""]:
            parts.append(str(val).strip())
    return "-".join(parts) if parts else None


def is_active_employee(status):
    """判断是否在职"""
    if pd.isna(status):
        return True  # 默认在职
    status_str = str(status).strip()
    # 离职状态
    if status_str in ["离职", "已离职"]:
        return False
    # 在职状态（包括试用期、实习期等）
    return True


def generate_employee_code(index, existing_codes):
    """生成员工编码"""
    code = f"EMP{index:04d}"
    while code in existing_codes:
        index += 1
        code = f"EMP{index:04d}"
    return code


def import_employees():
    """导入员工数据"""
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "ATE-人事档案系统.xlsx"
    )

    if not os.path.exists(excel_path):
        print(f"错误：找不到文件 {excel_path}")
        return

    print(f"读取 Excel 文件: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name="员工信息表")
    print(f"共 {len(df)} 条记录")

    db = SessionLocal()
    try:
        # 获取现有员工编码
        existing_codes = set()
        existing_employees = db.query(Employee.employee_code).all()
        for emp in existing_employees:
            existing_codes.add(emp.employee_code)

        # 获取管理员用户作为评估人
        admin_user = db.query(User).filter(User.username == "admin").first()
        evaluator_id = admin_user.id if admin_user else 1

        # 获取标签字典
        tags = db.query(HrTagDict).filter(HrTagDict.is_active == True).all()
        tag_dict = {tag.tag_name: tag for tag in tags}

        imported_count = 0
        updated_count = 0
        skipped_count = 0

        for idx, row in df.iterrows():
            name = clean_name(row.get("姓名"))
            if not name:
                skipped_count += 1
                continue

            department = get_department_name(row)
            position = (
                str(row.get("职务", "")).strip() if pd.notna(row.get("职务")) else None
            )
            phone = clean_phone(row.get("联系方式"))
            is_active = is_active_employee(row.get("在职离职状态"))
            entry_date = parse_entry_date(row.get("入职时间"))

            # 检查是否已存在（按姓名+部门匹配）
            existing = (
                db.query(Employee)
                .filter(Employee.name == name, Employee.department == department)
                .first()
            )

            if existing:
                # 更新现有员工
                existing.phone = phone or existing.phone
                existing.role = position or existing.role
                existing.is_active = is_active
                updated_count += 1
                employee = existing
            else:
                # 创建新员工
                employee_code = generate_employee_code(idx + 1, existing_codes)
                existing_codes.add(employee_code)

                employee = Employee(
                    employee_code=employee_code,
                    name=name,
                    department=department,
                    role=position,
                    phone=phone,
                    is_active=is_active,
                )
                db.add(employee)
                db.flush()  # 获取 ID
                imported_count += 1

            # 创建或更新员工档案
            profile = (
                db.query(HrEmployeeProfile)
                .filter(HrEmployeeProfile.employee_id == employee.id)
                .first()
            )

            if not profile:
                profile = HrEmployeeProfile(
                    employee_id=employee.id,
                    skill_tags=[],
                    domain_tags=[],
                    attitude_tags=[],
                    character_tags=[],
                    special_tags=[],
                    current_workload_pct=Decimal("0"),
                    total_projects=0,
                    profile_updated_at=datetime.now(),
                )
                db.add(profile)

            # 根据职位自动添加技能标签评估
            if position and is_active:
                skill_mappings = {
                    "PLC": ["PLC编程"],
                    "测试": ["ICT测试", "FCT测试"],
                    "机械": ["机械设计", "3D建模"],
                    "电气": ["电气原理图"],
                    "视觉": ["视觉系统"],
                    "客服": ["故障排除", "现场经验"],
                    "装配": ["装配调试"],
                    "HMI": ["HMI开发"],
                    "硬件": ["电气原理图"],
                    "软件": ["PLC编程", "HMI开发"],
                }

                matched_tags = set()
                for keyword, tag_names in skill_mappings.items():
                    if keyword in (position or ""):
                        for tag_name in tag_names:
                            if tag_name in tag_dict:
                                matched_tags.add(tag_name)

                # 添加标签评估
                for tag_name in matched_tags:
                    tag = tag_dict.get(tag_name)
                    if tag:
                        existing_eval = (
                            db.query(HrEmployeeTagEvaluation)
                            .filter(
                                HrEmployeeTagEvaluation.employee_id == employee.id,
                                HrEmployeeTagEvaluation.tag_id == tag.id,
                            )
                            .first()
                        )

                        if not existing_eval:
                            eval_record = HrEmployeeTagEvaluation(
                                employee_id=employee.id,
                                tag_id=tag.id,
                                score=3,  # 默认中等评分
                                evidence=f'根据职位 "{position}" 自动匹配',
                                evaluator_id=evaluator_id,
                                evaluate_date=datetime.now().date(),
                                is_valid=True,
                            )
                            db.add(eval_record)

            if (idx + 1) % 50 == 0:
                print(f"已处理 {idx + 1} 条记录...")
                db.commit()

        db.commit()
        print(f"\n导入完成:")
        print(f"  - 新增员工: {imported_count}")
        print(f"  - 更新员工: {updated_count}")
        print(f"  - 跳过记录: {skipped_count}")

        # 统计数据
        total_employees = db.query(Employee).count()
        active_employees = db.query(Employee).filter(Employee.is_active == True).count()
        total_profiles = db.query(HrEmployeeProfile).count()

        print(f"\n数据库统计:")
        print(f"  - 员工总数: {total_employees}")
        print(f"  - 在职员工: {active_employees}")
        print(f"  - 员工档案: {total_profiles}")

    except Exception as e:
        db.rollback()
        print(f"导入失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


def import_departments():
    """从员工数据中提取并导入部门结构"""
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "ATE-人事档案系统.xlsx"
    )

    df = pd.read_excel(excel_path, sheet_name="员工信息表")

    # 提取所有部门组合
    dept_hierarchy = {}
    for idx, row in df.iterrows():
        level1 = (
            str(row.get("一级部门", "")).strip()
            if pd.notna(row.get("一级部门"))
            else None
        )
        level2 = (
            str(row.get("二级部门", "")).strip()
            if pd.notna(row.get("二级部门"))
            else None
        )
        level3 = (
            str(row.get("三级部门", "")).strip()
            if pd.notna(row.get("三级部门"))
            else None
        )

        if level1 and level1 not in ["/", "NaN", ""]:
            if level1 not in dept_hierarchy:
                dept_hierarchy[level1] = {}

            if level2 and level2 not in ["/", "NaN", ""]:
                if level2 not in dept_hierarchy[level1]:
                    dept_hierarchy[level1][level2] = set()

                if level3 and level3 not in ["/", "NaN", ""]:
                    dept_hierarchy[level1][level2].add(level3)

    db = SessionLocal()
    try:
        dept_code_counter = 1

        for level1_name, level2_dict in dept_hierarchy.items():
            # 检查一级部门是否存在
            level1_dept = (
                db.query(Department)
                .filter(Department.dept_name == level1_name, Department.level == 1)
                .first()
            )

            if not level1_dept:
                level1_dept = Department(
                    dept_code=f"D{dept_code_counter:03d}",
                    dept_name=level1_name,
                    level=1,
                    is_active=True,
                )
                db.add(level1_dept)
                db.flush()
                dept_code_counter += 1

            for level2_name, level3_set in level2_dict.items():
                # 检查二级部门是否存在
                level2_dept = (
                    db.query(Department)
                    .filter(
                        Department.dept_name == level2_name,
                        Department.parent_id == level1_dept.id,
                    )
                    .first()
                )

                if not level2_dept:
                    level2_dept = Department(
                        dept_code=f"D{dept_code_counter:03d}",
                        dept_name=level2_name,
                        parent_id=level1_dept.id,
                        level=2,
                        is_active=True,
                    )
                    db.add(level2_dept)
                    db.flush()
                    dept_code_counter += 1

                for level3_name in level3_set:
                    # 检查三级部门是否存在
                    level3_dept = (
                        db.query(Department)
                        .filter(
                            Department.dept_name == level3_name,
                            Department.parent_id == level2_dept.id,
                        )
                        .first()
                    )

                    if not level3_dept:
                        level3_dept = Department(
                            dept_code=f"D{dept_code_counter:03d}",
                            dept_name=level3_name,
                            parent_id=level2_dept.id,
                            level=3,
                            is_active=True,
                        )
                        db.add(level3_dept)
                        dept_code_counter += 1

        db.commit()

        # 统计
        total_depts = db.query(Department).count()
        print(f"部门导入完成，共 {total_depts} 个部门")

    except Exception as e:
        db.rollback()
        print(f"部门导入失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
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
