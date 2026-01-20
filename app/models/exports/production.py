"""
生产和制造模型导出模块

包含：
- 生产管理
- 物料管理
- BOM管理
- 采购管理
"""

# 生产管理
from ..production import (
    AssemblyKit,
    EquipmentMaintenance,
    EquipmentUsageLog,
    ProductionLineStation,
    QualityInspection,
    Worker,
    WorkerAttendance,
    WorkerSkill,
    WorkOrder,
    WorkReport,
    Workshop,
    Workstation,
)

# 物料管理
from ..material import (
    BomHeader,
    BomItem,
    MaterialInventoryAlert,
    PurchaseOrder,
    PurchaseRequest,
)

# 短缺管理
from ..shortage import (
    KitCheck,
    MaterialArrival,
    MaterialRequirement,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageAlert,
    ShortageDailyReport,
    ShortageReport,
    WorkOrderBom,
)

__all__ = [
    # 生产
    "Workshop",
    "Workstation",
    "ProductionLineStation",
    "Worker",
    "WorkerSkill",
    "WorkerAttendance",
    "WorkOrder",
    "WorkReport",
    "AssemblyKit",
    "QualityInspection",
    "EquipmentMaintenance",
    "EquipmentUsageLog",
    # 物料
    "BomHeader",
    "BomItem",
    "PurchaseOrder",
    "PurchaseRequest",
    "MaterialInventoryAlert",
    # 短缺
    "ShortageReport",
    "ShortageDailyReport",
    "ShortageAlert",
    "MaterialRequirement",
    "MaterialTransfer",
    "MaterialSubstitution",
    "MaterialArrival",
    "KitCheck",
    "WorkOrderBom",
]
