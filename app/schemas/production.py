# -*- coding: utf-8 -*-
"""
生产管理模块 Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema, PaginatedResponse


# ==================== 车间管理 ====================

class WorkshopCreate(BaseModel):
    """创建车间"""
    workshop_code: str = Field(max_length=50, description="车间编码")
    workshop_name: str = Field(max_length=100, description="车间名称")
    workshop_type: str = Field(description="车间类型：MACHINING/ASSEMBLY/DEBUGGING等")
    manager_id: Optional[int] = Field(default=None, description="车间主管ID")
    location: Optional[str] = Field(default=None, max_length=200, description="车间位置")
    capacity_hours: Optional[Decimal] = Field(default=None, description="日产能(工时)")
    description: Optional[str] = Field(default=None, description="描述")
    is_active: Optional[bool] = Field(default=True, description="是否启用")


class WorkshopUpdate(BaseModel):
    """更新车间"""
    workshop_name: Optional[str] = None
    workshop_type: Optional[str] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None
    capacity_hours: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WorkshopResponse(TimestampSchema):
    """车间响应"""
    id: int
    workshop_code: str
    workshop_name: str
    workshop_type: str
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    location: Optional[str] = None
    capacity_hours: Optional[float] = None
    description: Optional[str] = None
    is_active: bool


class WorkshopListResponse(PaginatedResponse):
    """车间列表响应"""
    items: List[WorkshopResponse]


# ==================== 工位管理 ====================

class WorkstationCreate(BaseModel):
    """创建工位"""
    workstation_code: str = Field(max_length=50, description="工位编码")
    workstation_name: str = Field(max_length=100, description="工位名称")
    equipment_id: Optional[int] = Field(default=None, description="关联设备ID")
    description: Optional[str] = Field(default=None, description="描述")
    is_active: Optional[bool] = Field(default=True, description="是否启用")


class WorkstationUpdate(BaseModel):
    """更新工位"""
    workstation_name: Optional[str] = None
    equipment_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WorkstationResponse(TimestampSchema):
    """工位响应"""
    id: int
    workstation_code: str
    workstation_name: str
    workshop_id: int
    workshop_name: Optional[str] = None
    equipment_id: Optional[int] = None
    equipment_name: Optional[str] = None
    status: str
    current_worker_id: Optional[int] = None
    current_work_order_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool


class WorkstationStatusResponse(BaseModel):
    """工位状态响应"""
    workstation_id: int
    workstation_code: str
    workstation_name: str
    status: str
    current_worker_id: Optional[int] = None
    current_worker_name: Optional[str] = None
    current_work_order_id: Optional[int] = None
    current_work_order_no: Optional[str] = None
    is_available: bool


# ==================== 生产计划 ====================

class ProductionPlanCreate(BaseModel):
    """创建生产计划"""
    plan_name: str = Field(max_length=200, description="计划名称")
    plan_type: str = Field(description="计划类型：MASTER/WORKSHOP")
    project_id: Optional[int] = Field(default=None, description="关联项目ID")
    workshop_id: Optional[int] = Field(default=None, description="车间ID")
    plan_start_date: date = Field(description="计划开始日期")
    plan_end_date: date = Field(description="计划结束日期")
    description: Optional[str] = Field(default=None, description="计划说明")
    remark: Optional[str] = Field(default=None, description="备注")


class ProductionPlanUpdate(BaseModel):
    """更新生产计划"""
    plan_name: Optional[str] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    description: Optional[str] = None
    remark: Optional[str] = None


class ProductionPlanResponse(TimestampSchema):
    """生产计划响应"""
    id: int
    plan_no: str
    plan_name: str
    plan_type: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    plan_start_date: date
    plan_end_date: date
    status: str
    progress: int
    description: Optional[str] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    remark: Optional[str] = None


class ProductionPlanListResponse(PaginatedResponse):
    """生产计划列表响应"""
    items: List[ProductionPlanResponse]


# ==================== 生产工单 ====================

class WorkOrderCreate(BaseModel):
    """创建工单"""
    task_name: str = Field(max_length=200, description="任务名称")
    task_type: str = Field(description="工单类型：MACHINING/ASSEMBLY/DEBUGGING等")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    machine_id: Optional[int] = Field(default=None, description="机台ID")
    production_plan_id: Optional[int] = Field(default=None, description="生产计划ID")
    process_id: Optional[int] = Field(default=None, description="工序ID")
    workshop_id: Optional[int] = Field(default=None, description="车间ID")
    workstation_id: Optional[int] = Field(default=None, description="工位ID")
    material_id: Optional[int] = Field(default=None, description="物料ID")
    material_name: Optional[str] = Field(default=None, description="物料名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    drawing_no: Optional[str] = Field(default=None, description="图纸编号")
    plan_qty: int = Field(default=1, description="计划数量")
    standard_hours: Optional[Decimal] = Field(default=None, description="标准工时")
    plan_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    plan_end_date: Optional[date] = Field(default=None, description="计划结束日期")
    priority: str = Field(default="NORMAL", description="优先级")
    work_content: Optional[str] = Field(default=None, description="工作内容")
    remark: Optional[str] = Field(default=None, description="备注")


class WorkOrderUpdate(BaseModel):
    """更新工单"""
    task_name: Optional[str] = None
    plan_qty: Optional[int] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    priority: Optional[str] = None
    work_content: Optional[str] = None
    remark: Optional[str] = None


class WorkOrderAssignRequest(BaseModel):
    """工单派工请求"""
    worker_id: Optional[int] = Field(default=None, description="指派给(工人ID)")
    workstation_id: Optional[int] = Field(default=None, description="工位ID")


class WorkOrderResponse(TimestampSchema):
    """工单响应"""
    id: int
    work_order_no: str
    task_name: str
    task_type: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    production_plan_id: Optional[int] = None
    process_id: Optional[int] = None
    process_name: Optional[str] = None
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    workstation_id: Optional[int] = None
    workstation_name: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    plan_qty: int
    completed_qty: int
    qualified_qty: int
    defect_qty: int
    standard_hours: Optional[float] = None
    actual_hours: float
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    assigned_to: Optional[int] = None
    assigned_worker_name: Optional[str] = None
    status: str
    priority: str
    progress: int
    work_content: Optional[str] = None
    remark: Optional[str] = None


class WorkOrderListResponse(PaginatedResponse):
    """工单列表响应"""
    items: List[WorkOrderResponse]


class WorkReportItem(BaseModel):
    """报工记录项"""
    id: int
    report_no: str
    report_type: str
    report_time: datetime
    progress_percent: Optional[int] = None
    work_hours: Optional[float] = None
    completed_qty: Optional[int] = None
    qualified_qty: Optional[int] = None


class WorkOrderProgressResponse(BaseModel):
    """工单进度响应"""
    work_order_id: int
    work_order_no: str
    progress: int
    plan_qty: int
    completed_qty: int
    qualified_qty: int
    defect_qty: int
    standard_hours: Optional[float] = None
    actual_hours: float
    reports: Optional[List[WorkReportItem]] = Field(default=[], description="报工记录列表")


# ==================== 报工 ====================

class WorkReportStartRequest(BaseModel):
    """开工报告请求"""
    work_order_id: int = Field(description="工单ID")
    worker_id: int = Field(description="工人ID")
    report_note: Optional[str] = Field(default=None, description="报工说明")


class WorkReportProgressRequest(BaseModel):
    """进度上报请求"""
    work_order_id: int = Field(description="工单ID")
    worker_id: int = Field(description="工人ID")
    progress_percent: int = Field(ge=0, le=100, description="进度百分比")
    work_hours: Optional[Decimal] = Field(default=None, description="本次工时")
    report_note: Optional[str] = Field(default=None, description="报工说明")


class WorkReportCompleteRequest(BaseModel):
    """完工报告请求"""
    work_order_id: int = Field(description="工单ID")
    worker_id: int = Field(description="工人ID")
    completed_qty: int = Field(description="完成数量")
    qualified_qty: int = Field(description="合格数量")
    defect_qty: Optional[int] = Field(default=0, description="不良数量")
    work_hours: Optional[Decimal] = Field(default=None, description="本次工时")
    report_note: Optional[str] = Field(default=None, description="报工说明")


class WorkReportResponse(TimestampSchema):
    """报工响应"""
    id: int
    report_no: str
    work_order_id: int
    work_order_no: Optional[str] = None
    worker_id: int
    worker_name: Optional[str] = None
    report_type: str
    report_time: datetime
    progress_percent: Optional[int] = None
    work_hours: Optional[float] = None
    completed_qty: Optional[int] = None
    qualified_qty: Optional[int] = None
    defect_qty: Optional[int] = None
    status: str
    report_note: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None


class WorkReportListResponse(PaginatedResponse):
    """报工列表响应"""
    items: List[WorkReportResponse]


# ==================== 生产领料 ====================

class MaterialRequisitionItemCreate(BaseModel):
    """创建领料单明细"""
    material_id: int = Field(description="物料ID")
    request_qty: Decimal = Field(description="申请数量")
    remark: Optional[str] = None


class MaterialRequisitionCreate(BaseModel):
    """创建领料单"""
    work_order_id: Optional[int] = Field(default=None, description="关联工单ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    apply_reason: Optional[str] = Field(default=None, description="申请原因")
    items: List[MaterialRequisitionItemCreate] = Field(description="领料明细")
    remark: Optional[str] = None


class MaterialRequisitionItemResponse(BaseSchema):
    """领料单明细响应"""
    id: int
    requisition_id: int
    material_id: int
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    request_qty: Decimal
    approved_qty: Optional[Decimal] = None
    issued_qty: Optional[Decimal] = None
    unit: Optional[str] = None
    remark: Optional[str] = None


class MaterialRequisitionResponse(TimestampSchema):
    """领料单响应"""
    id: int
    requisition_no: str
    work_order_id: Optional[int] = None
    work_order_no: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    applicant_id: int
    applicant_name: Optional[str] = None
    apply_time: datetime
    apply_reason: Optional[str] = None
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approve_comment: Optional[str] = None
    issued_by: Optional[int] = None
    issued_at: Optional[datetime] = None
    items: List[MaterialRequisitionItemResponse] = []
    remark: Optional[str] = None


class MaterialRequisitionListResponse(PaginatedResponse):
    """领料单列表响应"""
    items: List[MaterialRequisitionResponse]


# ==================== 生产异常 ====================

class ProductionExceptionCreate(BaseModel):
    """创建生产异常"""
    exception_type: str = Field(description="异常类型：MATERIAL/EQUIPMENT/QUALITY/OTHER")
    exception_level: str = Field(default="MINOR", description="异常级别：MINOR/MAJOR/CRITICAL")
    title: str = Field(max_length=200, description="异常标题")
    description: Optional[str] = Field(default=None, description="异常描述")
    work_order_id: Optional[int] = Field(default=None, description="关联工单ID")
    project_id: Optional[int] = Field(default=None, description="关联项目ID")
    workshop_id: Optional[int] = Field(default=None, description="车间ID")
    equipment_id: Optional[int] = Field(default=None, description="设备ID")
    impact_hours: Optional[Decimal] = Field(default=None, description="影响工时(小时)")
    impact_cost: Optional[Decimal] = Field(default=None, description="影响成本(元)")
    remark: Optional[str] = None


class ProductionExceptionHandle(BaseModel):
    """处理生产异常"""
    handle_plan: str = Field(description="处理方案")
    handle_result: Optional[str] = Field(default=None, description="处理结果")


class ProductionExceptionResponse(TimestampSchema):
    """生产异常响应"""
    id: int
    exception_no: str
    exception_type: str
    exception_level: str
    title: str
    description: Optional[str] = None
    work_order_id: Optional[int] = None
    work_order_no: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    equipment_id: Optional[int] = None
    equipment_name: Optional[str] = None
    reporter_id: int
    reporter_name: Optional[str] = None
    report_time: datetime
    status: str
    handler_id: Optional[int] = None
    handler_name: Optional[str] = None
    handle_plan: Optional[str] = None
    handle_result: Optional[str] = None
    handle_time: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    impact_hours: Optional[Decimal] = None
    impact_cost: Optional[Decimal] = None
    remark: Optional[str] = None


class ProductionExceptionListResponse(PaginatedResponse):
    """生产异常列表响应"""
    items: List[ProductionExceptionResponse]


# ==================== 生产人员管理 ====================

class WorkerCreate(BaseModel):
    """创建生产人员"""
    worker_code: str = Field(max_length=50, description="工人编码")
    worker_name: str = Field(max_length=100, description="工人姓名")
    user_id: Optional[int] = Field(default=None, description="关联用户ID")
    workshop_id: Optional[int] = Field(default=None, description="所属车间ID")
    worker_type: Optional[str] = Field(default=None, description="工人类型")
    phone: Optional[str] = Field(default=None, max_length=20, description="联系电话")
    status: str = Field(default="ACTIVE", description="状态：ACTIVE/LEAVE/RESIGNED")
    remark: Optional[str] = None


class WorkerUpdate(BaseModel):
    """更新生产人员"""
    worker_name: Optional[str] = None
    workshop_id: Optional[int] = None
    worker_type: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class WorkerResponse(TimestampSchema):
    """生产人员响应"""
    id: int
    worker_code: str
    worker_name: str
    user_id: Optional[int] = None
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    worker_type: Optional[str] = None
    phone: Optional[str] = None
    status: str
    remark: Optional[str] = None


class WorkerListResponse(PaginatedResponse):
    """生产人员列表响应"""
    items: List[WorkerResponse]


# ==================== 生产报表 ====================

class ProductionDailyReportCreate(BaseModel):
    """创建生产日报"""
    report_date: date = Field(description="报告日期")
    workshop_id: Optional[int] = Field(default=None, description="车间ID(空表示全厂)")
    plan_qty: int = Field(default=0, description="计划数量")
    completed_qty: int = Field(default=0, description="完成数量")
    plan_hours: Optional[Decimal] = Field(default=0, description="计划工时")
    actual_hours: Optional[Decimal] = Field(default=0, description="实际工时")
    overtime_hours: Optional[Decimal] = Field(default=0, description="加班工时")
    should_attend: int = Field(default=0, description="应出勤人数")
    actual_attend: int = Field(default=0, description="实际出勤")
    leave_count: int = Field(default=0, description="请假人数")
    total_qty: int = Field(default=0, description="生产总数")
    qualified_qty: int = Field(default=0, description="合格数量")
    new_exception_count: int = Field(default=0, description="新增异常数")
    resolved_exception_count: int = Field(default=0, description="解决异常数")
    summary: Optional[str] = Field(default=None, description="日报总结")


class ProductionDailyReportResponse(TimestampSchema):
    """生产日报响应"""
    id: int
    report_date: date
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    plan_qty: int
    completed_qty: int
    completion_rate: Optional[float] = None
    plan_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    efficiency: Optional[float] = None
    should_attend: int
    actual_attend: int
    leave_count: int
    total_qty: int
    qualified_qty: int
    pass_rate: Optional[float] = None
    new_exception_count: int
    resolved_exception_count: int
    summary: Optional[str] = None
    created_by: Optional[int] = None


class ProductionDashboardResponse(BaseModel):
    """生产驾驶舱响应"""
    # 总体统计
    total_workshops: int = 0
    total_workstations: int = 0
    total_workers: int = 0
    active_workers: int = 0
    
    # 工单统计
    total_work_orders: int = 0
    pending_orders: int = 0
    in_progress_orders: int = 0
    completed_orders: int = 0
    
    # 今日统计
    today_plan_qty: int = 0
    today_completed_qty: int = 0
    today_completion_rate: float = 0.0
    today_actual_hours: float = 0.0
    
    # 质量统计
    today_qualified_qty: int = 0
    today_pass_rate: float = 0.0
    
    # 异常统计
    open_exceptions: int = 0
    critical_exceptions: int = 0
    
    # 设备统计
    total_equipment: int = 0
    running_equipment: int = 0
    maintenance_equipment: int = 0
    fault_equipment: int = 0
    
    # 车间统计
    workshop_stats: List[Dict[str, Any]] = []


class WorkshopTaskBoardResponse(BaseModel):
    """车间任务看板响应"""
    workshop_id: int
    workshop_name: str
    workstations: List[Dict[str, Any]] = []
    work_orders: List[Dict[str, Any]] = []
    workers: List[Dict[str, Any]] = []


class ProductionEfficiencyReportResponse(BaseModel):
    """生产效率报表响应"""
    report_date: date
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    plan_hours: float = 0.0
    actual_hours: float = 0.0
    efficiency: float = 0.0
    plan_qty: int = 0
    completed_qty: int = 0
    completion_rate: float = 0.0
    qualified_qty: int = 0
    pass_rate: float = 0.0


class CapacityUtilizationResponse(BaseModel):
    """产能利用率响应"""
    workshop_id: int
    workshop_name: str
    date: date
    capacity_hours: Optional[float] = None
    actual_hours: float = 0.0
    utilization_rate: float = 0.0
    plan_hours: float = 0.0
    load_rate: float = 0.0


class WorkerPerformanceReportResponse(BaseModel):
    """人员绩效报表响应"""
    worker_id: int
    worker_code: str
    worker_name: str
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    period_start: date
    period_end: date
    total_hours: float = 0.0
    total_reports: int = 0
    completed_orders: int = 0
    total_completed_qty: int = 0
    total_qualified_qty: int = 0
    average_efficiency: float = 0.0


class WorkerRankingResponse(BaseModel):
    """人员绩效排名响应"""
    rank: int
    worker_id: int
    worker_name: str
    workshop_name: Optional[str] = None
    efficiency: float = 0.0
    output: int = 0
    quality_rate: float = 0.0
    total_hours: float = 0.0
    score: float = 0.0

