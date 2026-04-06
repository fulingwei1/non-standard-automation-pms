# -*- coding: utf-8 -*-
"""
ECN成本影响服务 - 兼容模块

此模块作为 app.services.een.een_cost_impact_service 的别名，
用于向后兼容。
"""

# 重新导出所有公共接口
from app.services.ecn.ecn_cost_impact_service import (
    cost_impact_analysis,
    get_cost_tracking,
    create_cost_record,
    list_cost_records,
    approve_cost_record,
    get_project_ecn_cost_summary,
    check_cost_alerts,
    COST_TYPE_LABELS,
    DIRECT_COST_TYPES,
    INDIRECT_COST_TYPES,
)

__all__ = [
    "cost_impact_analysis",
    "get_cost_tracking", 
    "create_cost_record",
    "list_cost_records",
    "approve_cost_record",
    "get_project_ecn_cost_summary",
    "check_cost_alerts",
    "COST_TYPE_LABELS",
    "DIRECT_COST_TYPES",
    "INDIRECT_COST_TYPES",
]