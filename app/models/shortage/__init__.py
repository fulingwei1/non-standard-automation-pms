# -*- coding: utf-8 -*-
"""
缺料管理模型包

统一导出所有缺料管理相关的模型

注意: ShortageAlert 已废弃，缺料预警现使用统一的 AlertRecord 模型
通过 AlertRecord.target_type='SHORTAGE' 筛选缺料预警
详见: docs/plans/2026-01-21-alert-system-consolidation-design.md
"""
from .alerts import AlertHandleLog, ShortageDailyReport
from .arrivals import ArrivalFollowUp, MaterialArrival
from .handling import MaterialSubstitution, MaterialTransfer
from .reports import ShortageReport
from .requirements import KitCheck, MaterialRequirement, WorkOrderBom

__all__ = [
    # 缺料上报
    "ShortageReport",
    # 到货跟踪
    "MaterialArrival",
    "ArrivalFollowUp",
    # 物料处理
    "MaterialSubstitution",
    "MaterialTransfer",
    # 需求与检查
    "WorkOrderBom",
    "MaterialRequirement",
    "KitCheck",
    # 预警与统计
    "AlertHandleLog",
    "ShortageDailyReport",
    # ShortageAlert 已废弃 - 使用 AlertRecord.target_type='SHORTAGE'
]
