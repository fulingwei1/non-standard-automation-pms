# -*- coding: utf-8 -*-
"""
组织管理 - 辅助工具函数

通用数据清理函数已提取到 app/utils/common.py，
此处保留 re-export 以兼容现有导入。
"""

from typing import Dict, List, Optional

from app.common.tree_builder import build_tree
from app.models.organization import Department

# ── re-export 通用工具函数（向后兼容） ──────────────────────────
from app.utils.common import (  # noqa: F401
    clean_decimal,
    clean_name,
    clean_phone,
    clean_str,
    get_department_name,
    is_active_employee,
    parse_date,
)


def generate_employee_code(index: int, existing_codes: set) -> str:
    """生成员工编码"""
    code = f"EMP{index:04d}"
    while code in existing_codes:
        index += 1
        code = f"EMP{index:04d}"
    return code


def build_department_tree(departments: List[Department], parent_id: Optional[int] = None) -> List[Dict]:
    """构建部门树结构（使用通用 build_tree 实现）"""
    return build_tree(
        departments,
        parent_key="parent_id",
        to_dict=lambda dept: {
            "id": dept.id,
            "dept_code": dept.dept_code,
            "dept_name": dept.dept_name,
            "parent_id": dept.parent_id,
            "level": dept.level,
            "sort_order": dept.sort_order,
            "is_active": dept.is_active,
            "manager_id": dept.manager_id,
            "manager_name": dept.manager.name if dept.manager else None,
        },
        sort_key=lambda n: n.get("sort_order", 0),
        root_parent=parent_id,
    )
