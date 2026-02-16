# -*- coding: utf-8 -*-
"""
KPI服务模块

聚合所有KPI相关的服务函数，保持向后兼容
"""
from .crud import (
    create_kpi,
    delete_kpi,
    get_kpi,
    list_kpis,
    update_kpi,
)
from .data_source import (
    create_kpi_data_source,
    get_kpi_data_sources,
)
from .detail_history import (
    get_kpi_detail,
    get_kpi_history,
    get_kpi_with_history,
)
from .snapshot import create_kpi_snapshot
from .value import update_kpi_value

__all__ = [
    # CRUD
    "create_kpi",
    "get_kpi",
    "list_kpis",
    "update_kpi",
    "delete_kpi",
    # 值更新
    "update_kpi_value",
    # 详情和历史
    "get_kpi_detail",
    "get_kpi_history",
    "get_kpi_with_history",
    # 快照
    "create_kpi_snapshot",
    # 数据源
    "create_kpi_data_source",
    "get_kpi_data_sources",
]
