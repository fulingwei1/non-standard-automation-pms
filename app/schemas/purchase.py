# -*- coding: utf-8 -*-
"""
采购管理 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== 采购订单 ====================

class PurchaseOrderItemCreate(BaseModel):
    """采购订单明细创建"""
    material_id: Optional[int] = None
    bom_item_id: Optional[int] = None
    material_code: str = Field(max_length=50)
    material_name: str = Field(max_length=200)
    specification: Optional[str] = None
    unit: str = Field(default="件")
    quantity: Decimal = Field(gt=0, description="订购数量")
    unit_price: Decimal = Field(ge=0, description="单价")
    tax_rate: Decimal = Field(default=13, ge=0, le=100)
    required_date: Optional[date] = None
    remark: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    """创建采购订单"""
    supplier_id: int = Field(description="供应商ID")
    project_id: Optional[int] = None
    order_type: str = Field(default="NORMAL")
    order_title: Optional[str] = None
    required_date: Optional[date] = None
    payment_terms: Optional[str] = None
    delivery_address: Optional[str] = None
    contract_no: Optional[str] = None
    items: List[PurchaseOrderItemCreate] = Field(min_length=1)
    remark: Optional[str] = None


class PurchaseOrderUpdate(BaseModel):
    """更新采购订单"""
    order_title: Optional[str] = None
    required_date: Optional[date] = None
    promised_date: Optional[date] = None
    payment_terms: Optional[str] = None
    delivery_address: Optional[str] = None
    contract_no: Optional[str] = None
    remark: Optional[str] = None


class PurchaseOrderItemResponse(BaseSchema):
    """采购订单明细响应"""
    id: int
    item_no: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    tax_rate: Decimal
    amount_with_tax: Decimal
    required_date: Optional[date] = None
    promised_date: Optional[date] = None
    received_qty: Decimal = 0
    qualified_qty: Decimal = 0
    status: str = "PENDING"


class PurchaseOrderResponse(TimestampSchema):
    """采购订单响应"""
    id: int
    order_no: str
    supplier_id: int
    supplier_name: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    order_type: str
    order_title: Optional[str] = None
    total_amount: Decimal = 0
    tax_amount: Decimal = 0
    amount_with_tax: Decimal = 0
    order_date: Optional[date] = None
    required_date: Optional[date] = None
    status: str = "DRAFT"
    payment_status: str = "UNPAID"
    paid_amount: Decimal = 0
    items: List[PurchaseOrderItemResponse] = []


class PurchaseOrderListResponse(BaseSchema):
    """采购订单列表响应"""
    id: int
    order_no: str
    supplier_name: str
    project_name: Optional[str] = None
    total_amount: Decimal
    amount_with_tax: Decimal
    required_date: Optional[date] = None
    status: str
    payment_status: str
    created_at: datetime


# ==================== 收货单 ====================

class GoodsReceiptItemCreate(BaseModel):
    """收货明细创建"""
    order_item_id: int = Field(description="订单明细ID")
    delivery_qty: Decimal = Field(gt=0, description="送货数量")
    received_qty: Optional[Decimal] = None
    remark: Optional[str] = None


class GoodsReceiptCreate(BaseModel):
    """创建收货单"""
    order_id: int = Field(description="采购订单ID")
    receipt_date: date = Field(description="收货日期")
    receipt_type: str = Field(default="NORMAL")
    delivery_note_no: Optional[str] = None
    logistics_company: Optional[str] = None
    tracking_no: Optional[str] = None
    items: List[GoodsReceiptItemCreate] = Field(min_length=1)
    remark: Optional[str] = None


class GoodsReceiptItemResponse(BaseSchema):
    """收货明细响应"""
    id: int
    material_code: str
    material_name: str
    delivery_qty: Decimal
    received_qty: Decimal
    inspect_qty: Decimal = 0
    qualified_qty: Decimal = 0
    rejected_qty: Decimal = 0
    inspect_result: Optional[str] = None


class GoodsReceiptResponse(TimestampSchema):
    """收货单响应"""
    id: int
    receipt_no: str
    order_id: int
    order_no: str
    supplier_name: str
    receipt_date: date
    receipt_type: str
    status: str = "PENDING"
    inspect_status: str = "PENDING"
    items: List[GoodsReceiptItemResponse] = []


# ==================== 采购申请 ====================

class PurchaseRequestItemCreate(BaseModel):
    """采购申请明细创建"""
    bom_item_id: Optional[int] = None
    material_id: Optional[int] = None
    material_code: str = Field(max_length=50)
    material_name: str = Field(max_length=200)
    specification: Optional[str] = None
    unit: str = Field(default="件")
    quantity: Decimal = Field(gt=0, description="申请数量")
    unit_price: Decimal = Field(ge=0, description="预估单价")
    required_date: Optional[date] = None
    remark: Optional[str] = None


class PurchaseRequestCreate(BaseModel):
    """创建采购申请"""
    project_id: Optional[int] = None
    machine_id: Optional[int] = None
    request_type: str = Field(default="NORMAL")
    request_reason: Optional[str] = None
    required_date: Optional[date] = None
    items: List[PurchaseRequestItemCreate] = Field(min_length=1)
    remark: Optional[str] = None


class PurchaseRequestUpdate(BaseModel):
    """更新采购申请"""
    request_reason: Optional[str] = None
    required_date: Optional[date] = None
    remark: Optional[str] = None


class PurchaseRequestItemResponse(BaseSchema):
    """采购申请明细响应"""
    id: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    required_date: Optional[date] = None
    ordered_qty: Decimal = 0
    remark: Optional[str] = None


class PurchaseRequestResponse(TimestampSchema):
    """采购申请响应"""
    id: int
    request_no: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    request_type: str
    request_reason: Optional[str] = None
    required_date: Optional[date] = None
    total_amount: Decimal = 0
    status: str = "DRAFT"
    submitted_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_note: Optional[str] = None
    requested_by: Optional[int] = None
    requested_at: Optional[datetime] = None
    requester_name: Optional[str] = None
    approver_name: Optional[str] = None
    items: List[PurchaseRequestItemResponse] = []
    remark: Optional[str] = None


class PurchaseRequestListResponse(BaseSchema):
    """采购申请列表响应"""
    id: int
    request_no: str
    project_name: Optional[str] = None
    machine_name: Optional[str] = None
    total_amount: Decimal
    required_date: Optional[date] = None
    status: str
    requester_name: Optional[str] = None
    created_at: datetime
