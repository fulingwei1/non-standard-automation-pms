# -*- coding: utf-8 -*-
"""
生产管理 Schema 模块统一导出

模块结构:
 ├── workshop.py              # 车间管理 Schemas
 ├── workstation.py           # 工位管理 Schemas
 ├── production_plan.py      # 生产计划 Schemas
 ├── work_order.py           # 生产工单 Schemas
 ├── work_report.py          # 报工 Schemas
 ├── material_requisition.py # 生产领料 Schemas
 ├── production_exception.py # 生产异常 Schemas
 ├── worker.py               # 生产人员管理 Schemas
 └── production_reports.py   # 生产报表 Schemas
"""

# 车间管理
from .workshop import (
    WorkshopCreate,
    WorkshopListResponse,
    WorkshopResponse,
    WorkshopUpdate,
)

# 工位管理
from .workstation import (
    WorkstationCreate,
    WorkstationResponse,
    WorkstationStatusResponse,
    WorkstationUpdate,
)

# 生产计划
from .production_plan import (
    ProductionPlanCreate,
    ProductionPlanListResponse,
    ProductionPlanResponse,
    ProductionPlanUpdate,
)

# 生产工单
from .work_order import (
    WorkOrderAssignRequest,
    WorkOrderCreate,
    WorkOrderListResponse,
    WorkOrderProgressResponse,
    WorkOrderResponse,
    WorkOrderUpdate,
    WorkReportItem,
)

# 报工
from .work_report import (
    WorkReportCompleteRequest,
    WorkReportListResponse,
    WorkReportProgressRequest,
    WorkReportResponse,
    WorkReportStartRequest,
)

# 生产领料
from .material_requisition import (
    MaterialRequisitionCreate,
    MaterialRequisitionItemCreate,
    MaterialRequisitionItemResponse,
    MaterialRequisitionListResponse,
    MaterialRequisitionResponse,
)

# 生产异常
from .production_exception import (
    ProductionExceptionCreate,
    ProductionExceptionHandle,
    ProductionExceptionListResponse,
    ProductionExceptionResponse,
)

# 生产人员管理
from .worker import (
    WorkerCreate,
    WorkerListResponse,
    WorkerResponse,
    WorkerUpdate,
)

# 生产报表
from .production_reports import (
    CapacityUtilizationResponse,
    ProductionDashboardResponse,
    ProductionDailyReportCreate,
    ProductionDailyReportResponse,
    ProductionEfficiencyReportResponse,
    WorkerPerformanceReportResponse,
    WorkerRankingResponse,
    WorkshopTaskBoardResponse,
)

# 质量管理
from .quality import (
    BatchTracingRequest,
    BatchTracingResponse,
    CorrectiveActionCreate,
    CorrectiveActionResponse,
    DefectAnalysisCreate,
    DefectAnalysisResponse,
    ParetoAnalysisRequest,
    ParetoAnalysisResponse,
    ParetoDataPoint,
    QualityAlertListResponse,
    QualityAlertResponse,
    QualityAlertRuleCreate,
    QualityAlertRuleResponse,
    QualityInspectionCreate,
    QualityInspectionListResponse,
    QualityInspectionResponse,
    QualityStatisticsResponse,
    QualityTrendDataPoint,
    QualityTrendRequest,
    QualityTrendResponse,
    ReworkOrderCompleteRequest,
    ReworkOrderCreate,
    ReworkOrderListResponse,
    ReworkOrderResponse,
    SPCControlLimits,
    SPCDataPoint,
    SPCDataRequest,
    SPCDataResponse,
)

__all__ = [
    # 车间管理
    "WorkshopCreate",
    "WorkshopUpdate",
    "WorkshopResponse",
    "WorkshopListResponse",
    # 工位管理
    "WorkstationCreate",
    "WorkstationUpdate",
    "WorkstationResponse",
    "WorkstationStatusResponse",
    # 生产计划
    "ProductionPlanCreate",
    "ProductionPlanUpdate",
    "ProductionPlanResponse",
    "ProductionPlanListResponse",
    # 生产工单
    "WorkOrderCreate",
    "WorkOrderUpdate",
    "WorkOrderAssignRequest",
    "WorkOrderResponse",
    "WorkOrderListResponse",
    "WorkReportItem",
    "WorkOrderProgressResponse",
    # 报工
    "WorkReportStartRequest",
    "WorkReportProgressRequest",
    "WorkReportCompleteRequest",
    "WorkReportResponse",
    "WorkReportListResponse",
    # 生产领料
    "MaterialRequisitionItemCreate",
    "MaterialRequisitionCreate",
    "MaterialRequisitionItemResponse",
    "MaterialRequisitionResponse",
    "MaterialRequisitionListResponse",
    # 生产异常
    "ProductionExceptionCreate",
    "ProductionExceptionHandle",
    "ProductionExceptionResponse",
    "ProductionExceptionListResponse",
    # 生产人员管理
    "WorkerCreate",
    "WorkerUpdate",
    "WorkerResponse",
    "WorkerListResponse",
    # 生产报表
    "ProductionDailyReportCreate",
    "ProductionDailyReportResponse",
    "ProductionDashboardResponse",
    "WorkshopTaskBoardResponse",
    "ProductionEfficiencyReportResponse",
    "CapacityUtilizationResponse",
    "WorkerPerformanceReportResponse",
    "WorkerRankingResponse",
    # 质量管理
    "QualityInspectionCreate",
    "QualityInspectionResponse",
    "QualityInspectionListResponse",
    "QualityTrendRequest",
    "QualityTrendDataPoint",
    "QualityTrendResponse",
    "DefectAnalysisCreate",
    "DefectAnalysisResponse",
    "QualityAlertRuleCreate",
    "QualityAlertRuleResponse",
    "QualityAlertResponse",
    "QualityAlertListResponse",
    "ReworkOrderCreate",
    "ReworkOrderCompleteRequest",
    "ReworkOrderResponse",
    "ReworkOrderListResponse",
    "SPCDataRequest",
    "SPCDataPoint",
    "SPCControlLimits",
    "SPCDataResponse",
    "ParetoAnalysisRequest",
    "ParetoDataPoint",
    "ParetoAnalysisResponse",
    "QualityStatisticsResponse",
    "BatchTracingRequest",
    "BatchTracingResponse",
    "CorrectiveActionCreate",
    "CorrectiveActionResponse",
]
