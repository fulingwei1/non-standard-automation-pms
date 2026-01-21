# -*- coding: utf-8 -*-
"""
KPI数据采集器模块

聚合所有KPI数据采集相关的函数，保持向后兼容
"""
from .calculation import (
    auto_collect_kpi,
    batch_collect_kpis,
    calculate_formula,
    collect_kpi_value,
)
from .collectors import (
    collect_finance_metrics,
    collect_hr_metrics,
    collect_project_metrics,
    collect_purchase_metrics,
)
from .registry import get_collector, register_collector
from .status import get_collection_status

__all__ = [
    # 注册器
    "register_collector",
    "get_collector",
    # 模块采集器
    "collect_project_metrics",
    "collect_finance_metrics",
    "collect_purchase_metrics",
    "collect_hr_metrics",
    # 计算和采集
    "calculate_formula",
    "collect_kpi_value",
    "auto_collect_kpi",
    "batch_collect_kpis",
    # 状态查询
    "get_collection_status",
]
