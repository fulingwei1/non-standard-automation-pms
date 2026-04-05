# -*- coding: utf-8 -*-
"""
项目交付排产计划 Schema

用于 API 请求/响应验证
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 基础 Schema ====================

class ProjectDeliveryScheduleBase(BaseModel):
    """项目交付排产计划基础 Schema"""
    schedule_name: str = Field(..., description="计划名称", max_length=200)
    usage_type: str = Field(default="INTERNAL", description="使用类型：INTERNAL/CUSTOMER/BOTH")


class ProjectDeliveryScheduleCreate(ProjectDeliveryScheduleBase):
    """创建排产计划"""
    lead_id: Optional[int] = Field(None, description="商机 ID")
    project_id: Optional[int] = Field(None, description="项目 ID")
    project_template_id: Optional[int] = Field(None, description="项目模板 ID")
    departments: List[str] = Field(default_factory=list, description="需要填写的部门列表")


class ProjectDeliveryScheduleUpdate(BaseModel):
    """更新排产计划"""
    schedule_name: Optional[str] = Field(None, max_length=200)
    usage_type: Optional[str] = None
    status: Optional[str] = None
    version_comment: Optional[str] = None


class ProjectDeliveryScheduleResponse(ProjectDeliveryScheduleBase):
    """排产计划响应"""
    id: int
    schedule_no: str
    version: str
    status: str
    is_pre_contract: bool
    initiator_id: int
    initiator_name: str
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    contract_signed_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 任务 Schema ====================

class ProjectDeliveryTaskBase(BaseModel):
    """任务基础 Schema"""
    task_type: str = Field(..., description="任务类型")
    task_name: str = Field(..., description="任务名称", max_length=200)
    task_description: Optional[str] = None
    machine_name: Optional[str] = None
    module_name: Optional[str] = None
    assigned_engineer_id: Optional[int] = None
    assigned_engineer_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    planned_start: date
    planned_end: date
    estimated_hours: Decimal = Field(default=0, description="预估工时")


class ProjectDeliveryTaskCreate(ProjectDeliveryTaskBase):
    """创建任务"""
    schedule_id: int
    predecessor_tasks: Optional[List[int]] = Field(default_factory=list)
    dependency_type: str = Field(default="FS")
    lag_days: int = Field(default=0)


class ProjectDeliveryTaskUpdate(BaseModel):
    """更新任务"""
    task_name: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    estimated_hours: Optional[Decimal] = None
    assigned_engineer_id: Optional[int] = None
    status: Optional[str] = None
    progress_pct: Optional[Decimal] = None


class ProjectDeliveryTaskResponse(ProjectDeliveryTaskBase):
    """任务响应"""
    id: int
    task_no: str
    level: int
    has_conflict: bool
    conflict_details: Optional[Dict[str, Any]] = None
    status: str
    progress_pct: Decimal
    filled_by: Optional[int] = None
    filled_by_name: Optional[str] = None
    filled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 长周期采购 Schema ====================

class ProjectDeliveryLongCyclePurchaseBase(BaseModel):
    """长周期采购基础 Schema"""
    material_name: str = Field(..., description="物料名称", max_length=200)
    material_spec: Optional[str] = Field(None, max_length=500)
    material_category: Optional[str] = None
    supplier: Optional[str] = None
    supplier_contact: Optional[str] = None
    lead_time_days: int = Field(..., description="交期（天）")
    planned_order_date: Optional[date] = None
    planned_arrival_date: Optional[date] = None
    is_critical: bool = Field(default=False)


class ProjectDeliveryLongCyclePurchaseCreate(ProjectDeliveryLongCyclePurchaseBase):
    """创建长周期采购"""
    schedule_id: int


class ProjectDeliveryLongCyclePurchaseResponse(ProjectDeliveryLongCyclePurchaseBase):
    """长周期采购响应"""
    id: int
    item_no: str
    has_conflict: bool
    conflict_reason: Optional[str] = None
    filled_by: Optional[int] = None
    filled_by_name: Optional[str] = None
    filled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 机械设计任务 Schema ====================

class ProjectDeliveryMechanicalDesignBase(BaseModel):
    """机械设计任务基础 Schema"""
    design_type: str = Field(..., description="设计类型：3D_DESIGN/2D_DRAFTING/BOM")
    machine_name: Optional[str] = None
    module_name: Optional[str] = None
    designer_id: Optional[int] = None
    designer_name: Optional[str] = None
    planned_start: date
    planned_end: date
    estimated_hours: Decimal = Field(default=0)
    deliverables: Optional[List[str]] = None


class ProjectDeliveryMechanicalDesignCreate(ProjectDeliveryMechanicalDesignBase):
    """创建机械设计任务"""
    schedule_id: int


class ProjectDeliveryMechanicalDesignResponse(ProjectDeliveryMechanicalDesignBase):
    """机械设计任务响应"""
    id: int
    status: str
    filled_by: Optional[int] = None
    filled_by_name: Optional[str] = None
    filled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 变更日志 Schema ====================

class ProjectDeliveryChangeLogBase(BaseModel):
    """变更日志基础 Schema"""
    change_type: str = Field(..., description="变更类型")
    change_reason: str = Field(..., description="变更原因", max_length=500)
    change_description: Optional[str] = None
    version_from: Optional[str] = None
    version_to: Optional[str] = None


class ProjectDeliveryChangeLogCreate(ProjectDeliveryChangeLogBase):
    """创建变更日志"""
    schedule_id: int
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None


class ProjectDeliveryChangeLogResponse(ProjectDeliveryChangeLogBase):
    """变更日志响应"""
    id: int
    change_no: str
    changed_by: int
    changed_by_name: str
    changed_at: datetime
    notified_users: Optional[List[int]] = None
    notification_sent: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 甘特图数据 Schema ====================

class GanttTaskItem(BaseModel):
    """甘特图任务项"""
    id: int
    task_no: str
    name: str
    engineer: Optional[str] = None
    department: Optional[str] = None
    machine: Optional[str] = None
    module: Optional[str] = None
    start: date
    end: date
    hours: Decimal
    progress: Decimal
    has_conflict: bool
    predecessors: Optional[List[int]] = None


class GanttLongCyclePurchaseItem(BaseModel):
    """甘特图长周期采购项"""
    id: int
    item_no: str
    material: str
    supplier: Optional[str] = None
    lead_time: int
    order_date: Optional[date] = None
    arrival_date: Optional[date] = None
    is_critical: bool
    has_conflict: bool


class GanttDependencyItem(BaseModel):
    """甘特图依赖关系"""
    from_task: int
    to_task: int
    type: str
    lag_days: int


class GanttDataResponse(BaseModel):
    """甘特图数据响应"""
    schedule_id: int
    schedule_name: str
    version: str
    tasks: List[GanttTaskItem]
    long_cycle_purchases: List[GanttLongCyclePurchaseItem]
    dependencies: List[GanttDependencyItem]


# ==================== 冲突检测 Schema ====================

class EngineerConflictItem(BaseModel):
    """工程师冲突项"""
    engineer_id: int
    engineer_name: str
    task1_id: int
    task1_name: str
    task1_start: date
    task1_end: date
    task2_id: int
    task2_name: str
    task2_start: date
    task2_end: date
    overlap_days: int


class PurchaseConflictItem(BaseModel):
    """采购冲突项"""
    purchase_id: int
    material_name: str
    supplier: Optional[str]
    lead_time_days: int
    reason: str


class ConflictDetectionResponse(BaseModel):
    """冲突检测响应"""
    schedule_id: int
    has_conflicts: bool
    engineer_conflicts: List[EngineerConflictItem]
    purchase_conflicts: List[PurchaseConflictItem]
    total_conflicts: int


# ==================== 导出 Schema ====================

class ExportRequest(BaseModel):
    """导出请求"""
    format: str = Field(..., description="导出格式：excel/pdf/word")
    include_details: bool = Field(default=True, description="是否包含详细信息")


# ==================== 列表响应 Schema ====================

class ProjectDeliveryScheduleListResponse(BaseModel):
    """排产计划列表响应"""
    total: int
    items: List[ProjectDeliveryScheduleResponse]


class ProjectDeliveryTaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    items: List[ProjectDeliveryTaskResponse]
