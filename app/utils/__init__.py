# -*- coding: utf-8 -*-
"""
工具函数统一入口

推荐通过此模块导入常用工具，避免碎片化的导入路径。

示例::

    from app.utils import clean_str, parse_date, build_tree
    from app.utils import get_or_404, save_obj, delete_obj
    from app.utils import get_month_range, get_last_month_range
"""

# --- #54 通用清洗函数 (app.utils.common) ---
from app.utils.common import (  # noqa: F401
    clean_str,
    clean_name,
    clean_phone,
    clean_decimal,
    parse_date,
    get_department_name,
    is_active_employee,
)

# --- #55 树形结构 (app.utils.tree → app.common.tree_builder) ---
from app.utils.tree import build_tree  # noqa: F401

# --- DB helpers (app.utils.db_helpers) ---
from app.utils.db_helpers import get_or_404  # noqa: F401

# --- #57 时间范围 (app.common.date_range) ---
from app.common.date_range import (  # noqa: F401
    get_month_range,
    get_last_month_range,
    get_month_range_by_ym,
)
