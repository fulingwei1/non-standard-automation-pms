# -*- coding: utf-8 -*-
"""
项目核心管理 Schema
包含项目的创建、更新、响应模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import BaseSchema, TimestampSchema
from .machine import MachineResponse
from .milestone import MilestoneResponse


class ProjectCreate(BaseModel):
    """创建项目"""

    project_code: str = Field(max_length=50, description="项目编码")
    project_name: str = Field(max_length=200, description="项目名称")
    short_name: Optional[str] = Field(default=None, max_length=50)
    customer_id: Optional[int] = None
    contract_no: Optional[str] = None
    project_type: Optional[str] = None
    machine_count: int = Field(
        default=1, ge=1
    )  # Not in model but used in logic? check API. API commented it out.
    contract_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    contract_amount: Optional[Decimal] = Field(default=0)
    budget_amount: Optional[Decimal] = Field(default=0)
    pm_id: Optional[int] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目"""

    project_name: Optional[str] = None
    short_name: Optional[str] = None
    customer_id: Optional[int] = None
    contract_no: Optional[str] = None
    project_type: Optional[str] = None
    project_category: Optional[str] = None
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
    # 销售关联
    opportunity_id: Optional[int] = None
    contract_id: Optional[int] = None
    # ERP集成
    erp_synced: Optional[bool] = None
    erp_order_no: Optional[str] = None
    erp_sync_status: Optional[str] = None
    # 财务状态
    invoice_issued: Optional[bool] = None
    final_payment_completed: Optional[bool] = None
    final_payment_date: Optional[date] = None
    # 质保信息
    warranty_period_months: Optional[int] = None
    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    # 实施信息
    implementation_address: Optional[str] = None
    test_encryption: Optional[str] = None
    # 预立项关联
    initiation_id: Optional[int] = None


class ProjectResponse(TimestampSchema):
    """项目响应"""

    id: int
    project_code: str
    project_name: str
    short_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    project_type: Optional[str] = None
    project_category: Optional[str] = None
    industry: Optional[str] = None
    stage: str = "S1"
    status: Optional[str] = None
    health: str = "H1"
    progress_pct: Decimal = 0
    contract_date: Optional[date] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    contract_amount: Decimal = 0
    budget_amount: Decimal = 0
    actual_cost: Decimal = 0
    pm_id: Optional[int] = None
    pm_name: Optional[str] = None
    is_active: bool = True
    # 销售关联
    opportunity_id: Optional[int] = None
    contract_id: Optional[int] = None
    # ERP集成
    erp_synced: bool = False
    erp_sync_time: Optional[datetime] = None
    erp_order_no: Optional[str] = None
    erp_sync_status: str = "PENDING"
    # 财务状态
    invoice_issued: bool = False
    final_payment_completed: bool = False
    final_payment_date: Optional[date] = None
    # 质保信息
    warranty_period_months: Optional[int] = None
    warranty_start_date: Optional[date] = None
    warranty_end_date: Optional[date] = None
    # 实施信息
    implementation_address: Optional[str] = None
    test_encryption: Optional[str] = None
    # 预立项关联
    initiation_id: Optional[int] = None

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

    machines: List[MachineResponse] = []
    milestones: List[MilestoneResponse] = []
    members: List["ProjectMemberResponse"] = []


# 项目成员 Schema


class ProjectMemberCreate(BaseModel):
    """添加项目成员"""

    project_id: int
    user_id: int
    role_code: str = Field(max_length=50)
    allocation_pct: Decimal = Field(default=100, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    remark: Optional[str] = None


class ProjectMemberUpdate(BaseModel):
    """更新项目成员"""

    role_code: Optional[str] = None
    allocation_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    commitment_level: Optional[str] = None
    reporting_to_pm: Optional[bool] = None
    is_active: Optional[bool] = None
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


# 项目文档 Schema


class ProjectDocumentCreate(BaseModel):
    """创建文档记录"""

    project_id: Optional[int] = None
    rd_project_id: Optional[int] = None
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


class ProjectDocumentUpdate(BaseModel):
    """更新文档记录"""

    machine_id: Optional[int] = None
    doc_type: Optional[str] = None
    doc_category: Optional[str] = None
    doc_name: Optional[str] = None
    doc_no: Optional[str] = None
    version: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ProjectDocumentResponse(TimestampSchema):
    """文档记录响应"""

    id: int
    project_id: Optional[int] = None
    rd_project_id: Optional[int] = None
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
