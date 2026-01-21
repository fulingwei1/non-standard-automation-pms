# -*- coding: utf-8 -*-
"""
material_requisition Schemas

包含material_requisition相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..common import BaseSchema, PaginatedResponse, TimestampSchema


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


