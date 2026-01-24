# -*- coding: utf-8 -*-
"""
主模型导出 - 物料和采购相关
"""
from ...material import (
    BomHeader,
    BomItem,
    Material,
    MaterialCategory,
    MaterialShortage,
    MaterialSupplier,
)
from ...vendor import Vendor
from ...purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)
from ...shortage import (
    AlertHandleLog,
    ArrivalFollowUp,
    KitCheck,
    MaterialArrival,
    MaterialRequirement,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageDailyReport,
    ShortageReport,
    WorkOrderBom,
)
from ...assembly_kit import (
    AssemblyStage,
    AssemblyTemplate,
    BomItemAssemblyAttrs,
    CategoryStageMapping,
    MaterialReadiness,
    SchedulingSuggestion,
    ShortageAlertRule,
    ShortageDetail,
)

__all__ = [
    "Material",
    "MaterialCategory",
    "Vendor",
    "MaterialSupplier",
    "BomHeader",
    "BomItem",
    "MaterialShortage",
    "ShortageReport",
    "MaterialArrival",
    "ArrivalFollowUp",
    "MaterialSubstitution",
    "MaterialTransfer",
    "WorkOrderBom",
    "MaterialRequirement",
    "KitCheck",
    "AlertHandleLog",
    "ShortageDailyReport",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "GoodsReceipt",
    "GoodsReceiptItem",
    "PurchaseRequest",
    "PurchaseRequestItem",
    "AssemblyStage",
    "AssemblyTemplate",
    "CategoryStageMapping",
    "BomItemAssemblyAttrs",
    "MaterialReadiness",
    "ShortageDetail",
    "ShortageAlertRule",
    "SchedulingSuggestion",
]
