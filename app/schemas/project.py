# -*- coding: utf-8 -*-
"""
项目管理 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== 客户 ====================


class CustomerCreate(BaseModel):
    """创建客户"""

    customer_code: str = Field(max_length=50, description="客户编码")
    customer_name: str = Field(max_length=200, description="客户名称")
    short_name: Optional[str] = Field(default=None, max_length=50)
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    remark: Optional[str] = None


class CustomerUpdate(BaseModel):
    """更新客户"""

    customer_name: Optional[str] = None
    short_name: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    credit_level: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class CustomerResponse(TimestampSchema):
    """客户响应"""

    id: int
    customer_code: str
    customer_name: str
    short_name: Optional[str] = None
    customer_type: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    credit_level: str = "B"
    credit_limit: Optional[Decimal] = None
    status: str = "ACTIVE"
    legal_person: Optional[str] = None
    tax_no: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 项目 ====================


class ProjectCreate(BaseModel):
    """创建项目"""

    project_code: str = Field(max_length=50, description="项目编码")
    project_name: str = Field(max_length=200, description="项目名称")
    short_name: Optional[str] = Field(default=None, max_length=50)
    customer_id: Optional[int] = None
    contract_no: Optional[str] = None
    project_type: Optional[str] = None
    # product_category: Optional[str] = None
    # industry: Optional[str] = None
    # business_type & machine_count removed/mapped? Model has product_category/industry.
    # Keep it simple for now matching schema given to API logic.
    machine_count: int = Field(
        default=1, ge=1
    )  # Not in model but used in logic? check API. API commented it out.
    contract_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    # delivery_date: Optional[date] = None
    contract_amount: Optional[Decimal] = Field(default=0)
    budget_amount: Optional[Decimal] = Field(default=0)
    pm_id: Optional[int] = None
    description: Optional[str] = None
    # remark: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目"""

    project_name: Optional[str] = None
    short_name: Optional[str] = None
    customer_id: Optional[int] = None
    contract_no: Optional[str] = None
    project_type: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    health: Optional[str] = None
    progress_pct: Optional[Decimal] = None
    contract_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    contract_amount: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    pm_id: Optional[int] = None
    description: Optional[str] = None


class ProjectResponse(TimestampSchema):
    """项目响应"""

    id: int
    project_code: str
    project_name: str
    short_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    stage: str = "S1"
    status: Optional[str] = None
    health: str = "H1"
    progress_pct: Decimal = 0
    contract_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    # delivery_date: Optional[date] = None
    contract_amount: Decimal = 0
    budget_amount: Decimal = 0
    actual_cost: Decimal = 0
    pm_id: Optional[int] = None
    pm_name: Optional[str] = None
    # machine_count: int = 1
    is_active: bool = True

    class Config:
        from_attributes = True


class ProjectListResponse(BaseSchema):
    """项目列表响应"""

    id: int
    project_code: str
    project_name: str
    customer_name: Optional[str] = None
    stage: str
    health: str
    progress_pct: Decimal
    pm_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """项目详情响应"""

    machines: List["MachineResponse"] = []
    milestones: List["MilestoneResponse"] = []
    members: List["ProjectMemberResponse"] = []


# ==================== 设备 ====================


class MachineCreate(BaseModel):
    """创建设备"""

    machine_code: str = Field(max_length=50, description="设备编码")
    machine_name: str = Field(max_length=200, description="设备名称")
    project_id: int = Field(description="项目ID")
    machine_no: Optional[int] = 1
    machine_type: Optional[str] = None
    specification: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    remark: Optional[str] = None


class MachineUpdate(BaseModel):
    """更新设备"""

    machine_name: Optional[str] = None
    machine_no: Optional[int] = None
    machine_type: Optional[str] = None
    specification: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    health: Optional[str] = None
    progress_pct: Optional[Decimal] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    fat_date: Optional[date] = None
    fat_result: Optional[str] = None
    sat_date: Optional[date] = None
    sat_result: Optional[str] = None
    ship_date: Optional[date] = None
    ship_address: Optional[str] = None
    tracking_no: Optional[str] = None
    remark: Optional[str] = None


class MachineResponse(TimestampSchema):
    """设备响应"""

    id: int
    machine_code: str
    machine_name: str
    machine_no: int
    project_id: int
    project_name: Optional[str] = None
    machine_type: Optional[str] = None
    stage: str = "S1"
    status: str = "ST01"
    health: str = "H1"
    progress_pct: Decimal = 0
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None

    class Config:
        from_attributes = True


# ==================== 里程碑 ====================


class MilestoneCreate(BaseModel):
    """创建里程碑"""

    project_id: int = Field(description="项目ID")
    machine_id: Optional[int] = None
    milestone_code: str = Field(max_length=50, description="里程碑编码")
    milestone_name: str = Field(max_length=200, description="里程碑名称")
    milestone_type: str = Field(default="CUSTOM", description="里程碑类型")
    planned_date: date = Field(description="计划日期")
    stage_code: Optional[str] = None
    deliverables: Optional[str] = None
    owner_id: Optional[int] = None
    description: Optional[str] = None


class MilestoneUpdate(BaseModel):
    """更新里程碑"""

    milestone_name: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: Optional[str] = None
    deliverables: Optional[str] = None
    owner_id: Optional[int] = None
    description: Optional[str] = None
    completion_note: Optional[str] = None


class MilestoneResponse(TimestampSchema):
    """里程碑响应"""

    id: int
    project_id: int
    machine_id: Optional[int] = None
    milestone_code: str
    milestone_name: str
    milestone_type: str
    planned_date: date
    actual_date: Optional[date] = None
    status: str = "PENDING"
    stage_code: Optional[str] = None
    owner_id: Optional[int] = None


# ==================== 项目成员 ====================


class ProjectMemberCreate(BaseModel):
    """添加项目成员"""

    project_id: int
    user_id: int
    role_code: str = Field(max_length=50)
    allocation_pct: Decimal = Field(default=100, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    remark: Optional[str] = None


class ProjectMemberResponse(BaseSchema):
    """项目成员响应"""

    id: int
    project_id: int
    user_id: int
    username: str
    real_name: Optional[str] = None
    role_code: str
    allocation_pct: Decimal = 100
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    remark: Optional[str] = None


# ==================== 项目阶段 ====================


class ProjectStageCreate(BaseModel):
    """创建项目阶段（配置）"""

    project_id: int
    stage_code: str = Field(max_length=20)
    stage_name: str = Field(max_length=50)
    stage_order: int
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class ProjectStageUpdate(BaseModel):
    """更新项目阶段"""

    stage_name: Optional[str] = None
    stage_order: Optional[int] = None
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectStageResponse(TimestampSchema):
    """项目阶段响应"""

    id: int
    project_id: int
    stage_code: str
    stage_name: str
    stage_order: int
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None

    # 计划与进度
    progress_pct: int = 0
    status: str = "PENDING"
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None

    is_active: bool

    class Config:
        from_attributes = True


# ==================== 项目状态 ====================


class ProjectStatusCreate(BaseModel):
    """创建项目状态"""

    stage_id: int
    status_code: str
    status_name: str
    status_order: int
    description: Optional[str] = None
    status_type: str = "NORMAL"
    auto_next_status: Optional[str] = None


class ProjectStatusResponse(TimestampSchema):
    """项目状态响应"""

    id: int
    stage_id: int
    status_code: str
    status_name: str
    status_order: int
    description: Optional[str] = None
    status_type: str
    auto_next_status: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# ==================== 项目成本 ====================


class ProjectCostCreate(BaseModel):
    """创建成本记录"""

    project_id: int
    machine_id: Optional[int] = None
    cost_type: str = Field(max_length=50)
    cost_category: str = Field(max_length=50)
    source_module: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_no: Optional[str] = None
    amount: Decimal
    tax_amount: Optional[Decimal] = 0
    description: Optional[str] = None
    cost_date: date


class ProjectCostResponse(TimestampSchema):
    """成本记录响应"""

    id: int
    project_id: int
    machine_id: Optional[int] = None
    cost_type: str
    cost_category: str
    source_module: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    source_no: Optional[str] = None
    amount: Decimal
    tax_amount: Decimal
    description: Optional[str] = None
    cost_date: date

    class Config:
        from_attributes = True


# ==================== 项目文档 ====================


class ProjectDocumentCreate(BaseModel):
    """创建文档记录"""

    project_id: int
    machine_id: Optional[int] = None
    doc_type: str = Field(max_length=50)
    doc_category: Optional[str] = None
    doc_name: str = Field(max_length=200)
    doc_no: Optional[str] = None
    version: str = "1.0"
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    description: Optional[str] = None


class ProjectDocumentResponse(TimestampSchema):
    """文档记录响应"""

    id: int
    project_id: int
    machine_id: Optional[int] = None
    doc_type: str
    doc_category: Optional[str] = None
    doc_name: str
    doc_no: Optional[str] = None
    version: str
    file_path: str
    file_name: str
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[date] = None
    description: Optional[str] = None
    uploaded_by: Optional[int] = None

    class Config:
        from_attributes = True
