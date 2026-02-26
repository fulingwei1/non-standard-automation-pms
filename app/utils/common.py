# -*- coding: utf-8 -*-
"""
通用工具函数

从多处提取的共享数据清理/转换函数，统一维护。
原始位置：
  - app/api/v1/endpoints/organization/utils.py
  - app/services/hr_profile_import_service.py
  - app/services/employee_import_service.py
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional

import pandas as pd


def clean_str(val: Any) -> Optional[str]:
    """清理字符串值，去除换行和空白，过滤无效值"""
    if pd.isna(val):
        return None
    result = str(val).replace('\n', '').strip()
    if result in ('/', 'NaN', ''):
        return None
    return result


def clean_name(name: Any) -> Optional[str]:
    """清理姓名中的特殊字符"""
    if pd.isna(name):
        return None
    return str(name).replace('\n', '').strip()


def clean_phone(phone: Any) -> Optional[str]:
    """清理电话号码（处理科学计数法等）"""
    if pd.isna(phone):
        return None
    phone_str = str(phone)
    if 'e' in phone_str.lower() or '.' in phone_str:
        try:
            phone_str = str(int(float(phone)))
        except (ValueError, TypeError, OverflowError):
            pass
    return phone_str.strip()


def clean_decimal(val: Any) -> Optional[Decimal]:
    """清理数值，转为 Decimal"""
    if pd.isna(val):
        return None
    try:
        return Decimal(str(val))
    except (ValueError, TypeError, InvalidOperation):
        return None


def parse_date(date_val: Any) -> Optional[datetime]:
    """
    解析日期值，支持多种格式。

    Returns:
        解析后的 date 对象（注意：返回 date 而非 datetime）
    """
    if pd.isna(date_val):
        return None
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str):
        date_str = str(date_val).strip()
        if not date_str or date_str in ('/', 'NaN', '无试用期'):
            return None
        for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d', '%Y年%m月%d日']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
    return None


def get_department_name(row: dict, dept_cols: List[str]) -> Optional[str]:
    """组合部门名称（多级部门用 '-' 连接）"""
    parts = []
    for col in dept_cols:
        val = row.get(col)
        if pd.notna(val) and str(val).strip() not in ('/', 'NaN', ''):
            parts.append(str(val).strip())
    return '-'.join(parts) if parts else None


def is_active_employee(status: Any) -> bool:
    """判断是否在职"""
    if pd.isna(status):
        return True
    status_str = str(status).strip()
    if status_str in ('离职', '已离职'):
        return False
    return True
