# -*- coding: utf-8 -*-
"""
缺料管理扩展 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .common import BaseSchema, PaginatedResponse, TimestampSchema

# ==================== 缺料上报 ====================

class ShortageReportCreate(BaseModel):
    """创建缺料上报"""
    project_id: int = Field(description="项目ID")
    machine_id: Optional[int] = None
    work_order_id: Optional[int] = None
    material_id: int = Field(description="物料ID")
    required_qty: Decimal = Field(gt=0, description="需求数量")
    shortage_qty: Decimal = Field(gt=0, description="缺料数量")
    urgent_level: str = Field(default="NORMAL", description="紧急程度：NORMAL/URGENT/CRITICAL")
    report_location: Optional[str] = None
    remark: Optional[str] = None


class ShortageReportResponse(TimestampSchema):
    """缺料上报响应"""
    id: int
    report_no: str
    project_id: int
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    work_order_id: Optional[int] = None
    material_id: int
    material_code: str
    material_name: str
    required_qty: Decimal
    shortage_qty: Decimal
    urgent_level: str
    status: str
    reporter_id: int
    reporter_name: Optional[str] = None
    report_time: datetime
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    handler_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    solution_type: Optional[str] = None
    solution_note: Optional[str] = None
    remark: Optional[str] = None


class ShortageReportListResponse(PaginatedResponse):
    """缺料上报列表响应"""
    items: List[ShortageReportResponse]


# ==================== 到货跟踪 ====================

class MaterialArrivalCreate(BaseModel):
    """创建到货跟踪"""
    shortage_report_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    purchase_order_item_id: Optional[int] = None
    material_id: int = Field(description="物料ID")
    expected_qty: Decimal = Field(gt=0, description="预期到货数量")
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    expected_date: date = Field(description="预期到货日期")
    remark: Optional[str] = None


class ArrivalFollowUpCreate(BaseModel):
    """创建跟催记录"""
    follow_up_type: str = Field(default="CALL", description="跟催方式：CALL/EMAIL/VISIT/OTHER")
    follow_up_note: str = Field(description="跟催内容")
    supplier_response: Optional[str] = None
    next_follow_up_date: Optional[date] = None


class ArrivalFollowUpResponse(TimestampSchema):
    """到货跟催记录响应"""
    id: int
    arrival_id: int
    follow_up_type: str
    follow_up_note: str
    followed_by: int
    followed_by_name: Optional[str] = None
    followed_at: datetime
    supplier_response: Optional[str] = None
    next_follow_up_date: Optional[date] = None


class MaterialArrivalResponse(TimestampSchema):
    """到货跟踪响应"""
    id: int
    arrival_no: str
    shortage_report_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    material_id: int
    material_code: str
    material_name: str
    expected_qty: Decimal
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    expected_date: date
    actual_date: Optional[date] = None
    is_delayed: bool = False
    delay_days: int = 0
    status: str
    received_qty: Decimal = 0
    received_by: Optional[int] = None
    received_at: Optional[datetime] = None
    follow_up_count: int = 0
    remark: Optional[str] = None


class MaterialArrivalListResponse(PaginatedResponse):
    """到货跟踪列表响应"""
    items: List[MaterialArrivalResponse]


# ==================== 物料替代 ====================

class MaterialSubstitutionCreate(BaseModel):
    """创建物料替代申请"""
    shortage_report_id: Optional[int] = None
    project_id: int = Field(description="项目ID")
    bom_item_id: Optional[int] = None
    original_material_id: int = Field(description="原物料ID")
    substitute_material_id: int = Field(description="替代物料ID")
    original_qty: Decimal = Field(gt=0, description="原物料数量")
    substitute_qty: Decimal = Field(gt=0, description="替代物料数量")
    substitution_reason: str = Field(description="替代原因")
    technical_impact: Optional[str] = None
    cost_impact: Decimal = Field(default=0)
    remark: Optional[str] = None


class MaterialSubstitutionResponse(TimestampSchema):
    """物料替代响应"""
    id: int
    substitution_no: str
    project_id: int
    project_name: Optional[str] = None
    original_material_id: int
    original_material_code: str
    original_material_name: str
    original_qty: Decimal
    substitute_material_id: int
    substitute_material_code: str
    substitute_material_name: str
    substitute_qty: Decimal
    substitution_reason: str
    technical_impact: Optional[str] = None
    cost_impact: Decimal = 0
    status: str
    tech_approver_id: Optional[int] = None
    tech_approver_name: Optional[str] = None
    tech_approved_at: Optional[datetime] = None
    prod_approver_id: Optional[int] = None
    prod_approver_name: Optional[str] = None
    prod_approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    remark: Optional[str] = None


class MaterialSubstitutionListResponse(PaginatedResponse):
    """物料替代列表响应"""
    items: List[MaterialSubstitutionResponse]


# ==================== 物料调拨 ====================

class MaterialTransferCreate(BaseModel):
    """创建物料调拨申请"""
    shortage_report_id: Optional[int] = None
    from_project_id: Optional[int] = None
    from_location: Optional[str] = None
    to_project_id: int = Field(description="调入项目ID")
    to_location: Optional[str] = None
    material_id: int = Field(description="物料ID")
    transfer_qty: Decimal = Field(gt=0, description="调拨数量")
    transfer_reason: str = Field(description="调拨原因")
    urgent_level: str = Field(default="NORMAL", description="紧急程度")
    remark: Optional[str] = None


class MaterialTransferResponse(TimestampSchema):
    """物料调拨响应"""
    id: int
    transfer_no: str
    from_project_id: Optional[int] = None
    from_project_name: Optional[str] = None
    from_location: Optional[str] = None
    to_project_id: int
    to_project_name: Optional[str] = None
    to_location: Optional[str] = None
    material_id: int
    material_code: str
    material_name: str
    transfer_qty: Decimal
    available_qty: Decimal = 0
    transfer_reason: str
    urgent_level: str
    status: str
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    actual_qty: Optional[Decimal] = None
    remark: Optional[str] = None


class MaterialTransferListResponse(PaginatedResponse):
    """物料调拨列表响应"""
    items: List[MaterialTransferResponse]

