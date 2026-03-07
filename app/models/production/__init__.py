# -*- coding: utf-8 -*-
"""
生产管理模块 - 模型聚合层
"""

from .enums import (
    EquipmentStatusEnum,
    MaterialRequisitionStatusEnum,
    ProcessTypeEnum,
    ProductionExceptionLevelEnum,
    ProductionExceptionStatusEnum,
    ProductionExceptionTypeEnum,
    ProductionPlanStatusEnum,
    ProductionPlanTypeEnum,
    SkillLevelEnum,
    WorkerStatusEnum,
    WorkOrderPriorityEnum,
    WorkOrderStatusEnum,
    WorkOrderTypeEnum,
    WorkReportStatusEnum,
    WorkReportTypeEnum,
    WorkshopTypeEnum,
    WorkstationStatusEnum,
)
from .equipment import Equipment, EquipmentMaintenance
from .equipment_oee_record import EquipmentOEERecord
from .exception_handling_flow import (
    EscalationLevel,
    ExceptionHandlingFlow,
    FlowStatus,
)
from .exception_knowledge import ExceptionKnowledge
from .exception_pdca import ExceptionPDCA, PDCAStage
from .material import (
    MaterialRequisition,
    MaterialRequisitionItem,
    ProductionDailyReport,
)
from .material_tracking import (
    MaterialAlert,
    MaterialAlertRule,
    MaterialBatch,
    MaterialConsumption,
)
from .process import ProcessDict
from .production_exception import ProductionException
from .production_plan import ProductionPlan
from .production_progress_log import ProductionProgressLog
from .production_schedule import (
    ProductionResourceConflict,
    ProductionSchedule,
    ScheduleAdjustmentLog,
)
from .progress_alert import ProgressAlert
from .quality_inspection import (
    DefectAnalysis,
    QualityAlertRule,
    QualityInspection,
    ReworkOrder,
)
from .work_order import WorkOrder
from .work_report import WorkReport
from .worker import Worker, WorkerSkill
from .worker_efficiency_record import WorkerEfficiencyRecord
from .workshop import Workshop, Workstation
from .workstation_status import WorkstationStatus

__all__ = [
    # Enums
    "WorkshopTypeEnum",
    "WorkstationStatusEnum",
    "WorkerStatusEnum",
    "SkillLevelEnum",
    "ProductionPlanTypeEnum",
    "ProductionPlanStatusEnum",
    "WorkOrderTypeEnum",
    "WorkOrderStatusEnum",
    "WorkOrderPriorityEnum",
    "WorkReportTypeEnum",
    "WorkReportStatusEnum",
    "ProductionExceptionTypeEnum",
    "ProductionExceptionLevelEnum",
    "ProductionExceptionStatusEnum",
    "MaterialRequisitionStatusEnum",
    "EquipmentStatusEnum",
    "ProcessTypeEnum",
    # Models
    "Workshop",
    "Workstation",
    "Worker",
    "WorkerSkill",
    "ProcessDict",
    "Equipment",
    "EquipmentMaintenance",
    "EquipmentOEERecord",
    "WorkerEfficiencyRecord",
    "ProductionPlan",
    "WorkOrder",
    "WorkReport",
    "ProductionException",
    "MaterialRequisition",
    "MaterialRequisitionItem",
    "ProductionDailyReport",
    # Progress Tracking
    "ProductionProgressLog",
    "WorkstationStatus",
    "ProgressAlert",
    # Scheduling
    "ProductionSchedule",
    "ProductionResourceConflict",
    "ScheduleAdjustmentLog",
    # Quality Management
    "QualityInspection",
    "DefectAnalysis",
    "QualityAlertRule",
    "ReworkOrder",
    # Material Tracking
    "MaterialBatch",
    "MaterialConsumption",
    "MaterialAlert",
    "MaterialAlertRule",
    # Exception Enhancement
    "ExceptionHandlingFlow",
    "FlowStatus",
    "EscalationLevel",
    "ExceptionKnowledge",
    "ExceptionPDCA",
    "PDCAStage",
]
