# -*- coding: utf-8 -*-
"""
目标分解服务模块

提供从公司战略到部门目标到个人 KPI 的层层分解功能

模块结构:
 ├── department_objectives.py  # 部门目标管理
 ├── personal_kpis.py          # 个人 KPI 管理
 ├── decomposition_tree.py     # 分解追溯
 └── stats.py                  # 统计分析
"""

# 部门目标管理
from .department_objectives import (
    create_department_objective,
    delete_department_objective,
    get_department_objective,
    get_department_objective_detail,
    list_department_objectives,
    update_department_objective,
)

# 个人 KPI 管理
from .personal_kpis import (
    batch_create_personal_kpis,
    create_personal_kpi,
    delete_personal_kpi,
    get_personal_kpi,
    list_personal_kpis,
    manager_rating,
    self_rating,
    update_personal_kpi,
)

# 分解追溯
from .decomposition_tree import (
    get_decomposition_tree,
    trace_to_strategy,
)

# 统计分析
from .stats import (
    get_decomposition_stats,
)

__all__ = [
    # 部门目标管理
    "create_department_objective",
    "get_department_objective",
    "list_department_objectives",
    "update_department_objective",
    "delete_department_objective",
    "get_department_objective_detail",
    # 个人 KPI 管理
    "create_personal_kpi",
    "get_personal_kpi",
    "list_personal_kpis",
    "update_personal_kpi",
    "delete_personal_kpi",
    "self_rating",
    "manager_rating",
    "batch_create_personal_kpis",
    # 分解追溯
    "get_decomposition_tree",
    "trace_to_strategy",
    # 统计分析
    "get_decomposition_stats",
]
