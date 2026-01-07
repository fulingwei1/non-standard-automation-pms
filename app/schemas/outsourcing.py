# -*- coding: utf-8 -*-
"""
外协管理 Schema
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== 外协商 ====================

class VendorCreate(BaseModel):
    """创建外协商"""
    vendor_code: str = Field(max_length=50)
    vendor_name: str = Field(max_length=200)
    vendor_short_name: Optional[str] = None
    vendor_type: str = Field(description="MACHINING/ASSEMBLY/SURFACE/ELECTRICAL/OTHER")
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    business_license: Optional[str] = None
    qualification: Optional[List[Any]] = None
    capabilities: Optional[List[Any]] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_number: Optional[str] = None
    remark: Optional[str] = None


class VendorUpdate(BaseModel):
    """更新外协商"""
    vendor_name: Optional[str] = None
    vendor_short_name: Optional[str] = None
    vendor_type: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_number: Optional[str] = None
    remark: Optional[str] = None


class VendorResponse(TimestampSchema):
    """外协商响应"""
    id: int
    vendor_code: str
    vendor_name: str
    vendor_short_name: Optional[str] = None
    vendor_type: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    quality_rating: Decimal = 0
    delivery_rating: Decimal = 0
    service_rating: Decimal = 0
    overall_rating: Decimal = 0
    status: str = "ACTIVE"
    cooperation_start: Optional[date] = None
    last_order_date: Optional[date] = None


# ==================== 外协订单 ====================

class OutsourcingOrderItemCreate(BaseModel):
    """外协订单明细创建"""
    material_id: Optional[int] = None
    material_code: str = Field(max_length=50)
    material_name: str = Field(max_length=200)
    specification: Optional[str] = None
    drawing_no: Optional[str] = None
    process_type: Optional[str] = None
    process_content: Optional[str] = None
    process_requirements: Optional[str] = None
    unit: str = Field(default="件")
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    material_provided: bool = False
    provided_quantity: Optional[Decimal] = Field(default=0)
    remark: Optional[str] = None


class OutsourcingOrderCreate(BaseModel):
    """创建外协订单"""
    vendor_id: int = Field(description="外协商ID")
    project_id: int = Field(description="项目ID")
    machine_id: Optional[int] = None
    order_type: str = Field(description="MACHINING/ASSEMBLY/SURFACE/OTHER")
    order_title: str = Field(max_length=200)
    order_description: Optional[str] = None
    tax_rate: Decimal = Field(default=13, ge=0, le=100)
    required_date: Optional[date] = None
    contract_no: Optional[str] = None
    items: List[OutsourcingOrderItemCreate] = Field(min_length=1)
    remark: Optional[str] = None


class OutsourcingOrderUpdate(BaseModel):
    """更新外协订单"""
    order_title: Optional[str] = None
    order_description: Optional[str] = None
    required_date: Optional[date] = None
    estimated_date: Optional[date] = None
    contract_no: Optional[str] = None
    remark: Optional[str] = None


class OutsourcingOrderItemResponse(BaseSchema):
    """外协订单明细响应"""
    id: int
    item_no: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    drawing_no: Optional[str] = None
    process_type: Optional[str] = None
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    material_provided: bool = False
    delivered_quantity: Decimal = 0
    qualified_quantity: Decimal = 0
    rejected_quantity: Decimal = 0
    status: str = "PENDING"


class OutsourcingOrderResponse(TimestampSchema):
    """外协订单响应"""
    id: int
    order_no: str
    vendor_id: int
    vendor_name: str
    project_id: int
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    order_type: str
    order_title: str
    total_amount: Decimal = 0
    tax_rate: Decimal = 13
    tax_amount: Decimal = 0
    amount_with_tax: Decimal = 0
    required_date: Optional[date] = None
    estimated_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: str = "DRAFT"
    payment_status: str = "UNPAID"
    paid_amount: Decimal = 0
    items: List[OutsourcingOrderItemResponse] = []


class OutsourcingOrderListResponse(BaseSchema):
    """外协订单列表响应"""
    id: int
    order_no: str
    vendor_name: str
    project_name: Optional[str] = None
    order_type: str
    order_title: str
    amount_with_tax: Decimal
    required_date: Optional[date] = None
    status: str
    payment_status: str
    created_at: datetime


# ==================== 外协交付 ====================

class OutsourcingDeliveryItemCreate(BaseModel):
    """交付明细创建"""
    order_item_id: int
    delivery_quantity: Decimal = Field(gt=0)
    remark: Optional[str] = None


class OutsourcingDeliveryCreate(BaseModel):
    """创建交付单"""
    order_id: int
    delivery_date: date
    delivery_type: str = Field(default="NORMAL")
    delivery_person: Optional[str] = None
    logistics_company: Optional[str] = None
    tracking_no: Optional[str] = None
    items: List[OutsourcingDeliveryItemCreate] = Field(min_length=1)
    remark: Optional[str] = None


class OutsourcingDeliveryResponse(TimestampSchema):
    """交付单响应"""
    id: int
    delivery_no: str
    order_id: int
    order_no: str
    vendor_name: str
    delivery_date: date
    delivery_type: str
    status: str = "PENDING"
    received_at: Optional[datetime] = None


# ==================== 外协质检 ====================

class OutsourcingInspectionCreate(BaseModel):
    """创建质检"""
    delivery_id: int
    delivery_item_id: int
    inspect_type: str = Field(default="INCOMING")
    inspect_date: date
    inspect_quantity: Decimal = Field(gt=0)
    sample_quantity: Optional[Decimal] = Field(default=0)
    qualified_quantity: Decimal = Field(ge=0)
    rejected_quantity: Decimal = Field(ge=0)
    inspect_result: str = Field(description="PASSED/REJECTED/CONDITIONAL")
    defect_description: Optional[str] = None
    defect_type: Optional[str] = None
    disposition: Optional[str] = None
    disposition_note: Optional[str] = None
    remark: Optional[str] = None


class OutsourcingInspectionResponse(TimestampSchema):
    """质检响应"""
    id: int
    inspection_no: str
    delivery_id: int
    inspect_type: str
    inspect_date: date
    inspector_name: Optional[str] = None
    inspect_quantity: Decimal
    qualified_quantity: Decimal
    rejected_quantity: Decimal
    inspect_result: Optional[str] = None
    pass_rate: Decimal = 0
    disposition: Optional[str] = None


# ==================== 外协进度 ====================

class OutsourcingProgressCreate(BaseModel):
    """创建进度报告"""
    order_id: int
    order_item_id: Optional[int] = None
    report_date: date
    progress_pct: int = Field(ge=0, le=100)
    completed_quantity: Optional[Decimal] = Field(default=0)
    current_process: Optional[str] = None
    next_process: Optional[str] = None
    estimated_complete: Optional[date] = None
    issues: Optional[str] = None
    risk_level: Optional[str] = None
    attachments: Optional[List[Any]] = None


class OutsourcingProgressResponse(TimestampSchema):
    """进度报告响应"""
    id: int
    order_id: int
    report_date: date
    progress_pct: int
    completed_quantity: Decimal = 0
    current_process: Optional[str] = None
    estimated_complete: Optional[date] = None
    issues: Optional[str] = None
    risk_level: Optional[str] = None


# ==================== 外协付款 ====================

class OutsourcingPaymentCreate(BaseModel):
    """创建外协付款"""
    vendor_id: int = Field(description="外协商ID")
    order_id: Optional[int] = Field(default=None, description="外协订单ID")
    payment_type: str = Field(description="ADVANCE/PROGRESS/FINAL/OTHER")
    payment_amount: Decimal = Field(gt=0, description="付款金额")
    payment_date: date = Field(description="付款日期")
    payment_method: str = Field(description="BANK_TRANSFER/CHECK/CASH/OTHER")
    invoice_no: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    remark: Optional[str] = None


class OutsourcingPaymentUpdate(BaseModel):
    """更新外协付款"""
    payment_amount: Optional[Decimal] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    invoice_no: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    remark: Optional[str] = None


class OutsourcingPaymentResponse(TimestampSchema):
    """外协付款响应"""
    id: int
    payment_no: str
    vendor_id: int
    vendor_name: Optional[str] = None
    order_id: Optional[int] = None
    order_no: Optional[str] = None
    payment_type: str
    payment_amount: Decimal
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    invoice_no: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    status: str = "DRAFT"
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    remark: Optional[str] = None
