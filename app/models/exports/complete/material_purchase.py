# -*- coding: utf-8 -*-
"""
完整模型导出 - 物料和采购相关
"""
# 物料管理
from ...material import (
    BomHeader,
    BomItem,
    Material,
    MaterialCategory,
    MaterialSupplier,
)
from ...vendor import Vendor

# 采购管理
from ...purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)

# 短缺管理
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

# 装配套件分析
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
    # Material
    "Material",
    "MaterialCategory",
    "Vendor",
    "MaterialSupplier",
    "BomHeader",
    "BomItem",
    # Purchase
    "PurchaseOrder",
    "PurchaseOrderItem",
    "GoodsReceipt",
    "GoodsReceiptItem",
    "PurchaseRequest",
    "PurchaseRequestItem",
    # Shortage
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
    # ShortageAlert 已废弃 - 使用 AlertRecord.target_type='SHORTAGE'
    # Assembly Kit
    "AssemblyStage",
    "AssemblyTemplate",
    "CategoryStageMapping",
    "BomItemAssemblyAttrs",
    "MaterialReadiness",
    "ShortageDetail",
    "ShortageAlertRule",
    "SchedulingSuggestion",
]
