# -*- coding: utf-8 -*-
"""
组织管理 - 辅助工具函数
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

import pandas as pd

from app.models.organization import Department


def build_department_tree(departments: List[Department], parent_id: Optional[int] = None) -> List[Dict]:
    """构建部门树结构"""
    tree = []
    for dept in departments:
        if dept.parent_id == parent_id:
            children = build_department_tree(departments, dept.id)
            dept_dict = {
                "id": dept.id,
                "dept_code": dept.dept_code,
                "dept_name": dept.dept_name,
                "parent_id": dept.parent_id,
                "level": dept.level,
                "sort_order": dept.sort_order,
                "is_active": dept.is_active,
                "manager_id": dept.manager_id,
                "manager_name": dept.manager.name if dept.manager else None,
                "children": children if children else None,
            }
            tree.append(dept_dict)
    return sorted(tree, key=lambda x: x.get("sort_order", 0))


def clean_name(name: Any) -> Optional[str]:
    """清理姓名中的特殊字符"""
    if pd.isna(name):
        return None
    return str(name).replace('\n', '').strip()


def clean_phone(phone: Any) -> Optional[str]:
    """清理电话号码"""
    if pd.isna(phone):
        return None
    phone_str = str(phone)
    if 'e' in phone_str.lower() or '.' in phone_str:
        try:
            phone_str = str(int(float(phone)))
        except (ValueError, TypeError, OverflowError):
            pass
    return phone_str.strip()


def get_department_name(row: Dict, dept_cols: List[str]) -> Optional[str]:
    """组合部门名称"""
    parts = []
    for col in dept_cols:
        val = row.get(col)
        if pd.notna(val) and str(val).strip() not in ['/', 'NaN', '']:
            parts.append(str(val).strip())
    return '-'.join(parts) if parts else None


def is_active_employee(status: Any) -> bool:
    """判断是否在职"""
    if pd.isna(status):
        return True
    status_str = str(status).strip()
    if status_str in ['离职', '已离职']:
        return False
    return True


def generate_employee_code(index: int, existing_codes: set) -> str:
    """生成员工编码"""
    code = f"EMP{index:04d}"
    while code in existing_codes:
        index += 1
        code = f"EMP{index:04d}"
    return code


def parse_date(date_val: Any) -> Optional[datetime]:
    """解析日期值"""
    if pd.isna(date_val):
        return None
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str):
        date_str = str(date_val).strip()
        if not date_str or date_str in ['/', 'NaN', '无试用期']:
            return None
        for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d', '%Y年%m月%d日']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
    return None


def clean_str(val: Any) -> Optional[str]:
    """清理字符串值"""
    if pd.isna(val):
        return None
    result = str(val).replace('\n', '').strip()
    if result in ['/', 'NaN', '']:
        return None
    return result


def clean_decimal(val: Any) -> Optional[Decimal]:
    """清理数值"""
    if pd.isna(val):
        return None
    try:
        return Decimal(str(val))
    except (ValueError, TypeError, InvalidOperation):
        return None
