# -*- coding: utf-8 -*-
"""
完整模型导出 - 生产和外协相关
"""

# 生产管理
from ...production import (
    Equipment,
    EquipmentMaintenance,
    MaterialRequisition,
    MaterialRequisitionItem,
    ProcessDict,
    ProductionDailyReport,
    ProductionException,
    ProductionPlan,
    Worker,
    WorkerSkill,
    WorkOrder,
    WorkReport,
    Workshop,
    Workstation,
)

# 外协管理
from ...outsourcing import (
    OutsourcingDelivery,
    OutsourcingDeliveryItem,
    OutsourcingEvaluation,
    OutsourcingInspection,
    OutsourcingOrder,
    OutsourcingOrderItem,
    OutsourcingPayment,
    OutsourcingProgress,
)

__all__ = [
    # Production
    "Workshop",
    "Workstation",
    "Worker",
    "WorkerSkill",
    "ProcessDict",
    "Equipment",
    "EquipmentMaintenance",
    "ProductionPlan",
    "WorkOrder",
    "WorkReport",
    "ProductionException",
    "MaterialRequisition",
    "MaterialRequisitionItem",
    "ProductionDailyReport",
    # Outsourcing
    "OutsourcingOrder",
    "OutsourcingOrderItem",
    "OutsourcingDelivery",
    "OutsourcingDeliveryItem",
    "OutsourcingInspection",
    "OutsourcingPayment",
    "OutsourcingEvaluation",
    "OutsourcingProgress",
]
