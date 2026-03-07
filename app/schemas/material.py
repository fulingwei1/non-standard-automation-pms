# -*- coding: utf-8 -*-
"""
物料管理 Schema
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from .common import BaseSchema, TimestampSchema

# ==================== 物料分类 ====================

class MaterialCategoryCreate(BaseModel):
    """创建物料分类"""
    category_code: str = Field(max_length=50)
    category_name: str = Field(max_length=100)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0


class MaterialCategoryResponse(TimestampSchema):
    """物料分类响应"""
    id: int
    category_code: str
    category_name: str
    parent_id: Optional[int] = None
    level: Optional[int] = 1
    full_path: Optional[str] = None
    is_active: Optional[bool] = True
    children: List['MaterialCategoryResponse'] = []

    @field_validator("level", mode="before")
    @classmethod
    def _normalize_level(cls, v):
        return 1 if v is None else v

    @field_validator("is_active", mode="before")
    @classmethod
    def _normalize_is_active(cls, v):
        return True if v is None else v


# ==================== 物料 ====================

class MaterialCreate(BaseModel):
    """创建物料"""
    material_code: Optional[str] = Field(default=None, max_length=50, description="物料编码（不提供则根据类别自动生成）")
    material_name: str = Field(max_length=200, description="物料名称")
    category_id: Optional[int] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: str = Field(default="件", max_length=20)
    drawing_no: Optional[str] = None
    material_type: Optional[str] = None
    source_type: str = Field(default="PURCHASE")
    standard_price: Optional[Decimal] = Field(default=0)
    safety_stock: Optional[Decimal] = Field(default=0)
    lead_time_days: int = Field(default=0, ge=0)
    min_order_qty: Optional[Decimal] = Field(default=1)
    default_supplier_id: Optional[int] = None
    is_key_material: bool = False
    remark: Optional[str] = None


class MaterialUpdate(BaseModel):
    """更新物料"""
    material_name: Optional[str] = None
    category_id: Optional[int] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    drawing_no: Optional[str] = None
    material_type: Optional[str] = None
    source_type: Optional[str] = None
    standard_price: Optional[Decimal] = None
    safety_stock: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    min_order_qty: Optional[Decimal] = None
    default_supplier_id: Optional[int] = None
    is_key_material: Optional[bool] = None
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class MaterialResponse(TimestampSchema):
    """物料响应"""
    id: int
    material_code: Optional[str] = ""
    material_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = "件"
    material_type: Optional[str] = None
    source_type: Optional[str] = "PURCHASE"
    standard_price: Optional[Decimal] = Decimal("0")
    last_price: Optional[Decimal] = Decimal("0")
    safety_stock: Optional[Decimal] = Decimal("0")
    current_stock: Optional[Decimal] = Decimal("0")
    lead_time_days: Optional[int] = 0
    is_key_material: Optional[bool] = False
    is_active: Optional[bool] = True

    @field_validator("material_code", mode="before")
    @classmethod
    def _normalize_material_code(cls, v):
        return "" if v is None else v

    @field_validator("unit", mode="before")
    @classmethod
    def _normalize_unit(cls, v):
        return "件" if v is None else v

    @field_validator("source_type", mode="before")
    @classmethod
    def _normalize_source_type(cls, v):
        return "PURCHASE" if v is None else v

    @field_validator("standard_price", "last_price", "safety_stock", "current_stock", mode="before")
    @classmethod
    def _normalize_decimal_fields(cls, v):
        return Decimal("0") if v is None else v

    @field_validator("lead_time_days", mode="before")
    @classmethod
    def _normalize_lead_time_days(cls, v):
        return 0 if v is None else v

    @field_validator("is_key_material", "is_active", mode="before")
    @classmethod
    def _normalize_bool_fields(cls, v, info):
        if v is None:
            return False if info.field_name == "is_key_material" else True
        return v


class WarehouseStatistics(BaseModel):
    """仓储统计（给生产总监看）"""
    total_items: int = 0
    in_stock_items: int = 0
    low_stock_items: int = 0
    out_of_stock_items: int = 0
    inventory_turnover: float = 0.0
    warehouse_utilization: float = 0.0
    pending_inbound: int = 0
    pending_outbound: int = 0


class MaterialSearchResponse(BaseModel):
    """物料查找响应"""
    material_id: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    category: Optional[str] = None
    current_stock: float = 0.0
    safety_stock: float = 0.0
    in_transit_qty: float = 0.0
    available_qty: float = 0.0
    unit: str = "件"
    unit_price: float = 0.0
    supplier_name: Optional[str] = None


# ==================== 供应商 ====================

class SupplierCreate(BaseModel):
    """创建供应商"""
    supplier_code: str = Field(max_length=50, description="供应商编码")
    supplier_name: str = Field(max_length=200, description="供应商名称")
    supplier_short_name: Optional[str] = None
    supplier_type: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    business_license: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_number: Optional[str] = None
    payment_terms: Optional[str] = None
    remark: Optional[str] = None


class SupplierUpdate(BaseModel):
    """更新供应商"""
    supplier_name: Optional[str] = None
    supplier_short_name: Optional[str] = None
    supplier_type: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    supplier_level: Optional[str] = None
    status: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    tax_number: Optional[str] = None
    payment_terms: Optional[str] = None
    remark: Optional[str] = None


class SupplierResponse(TimestampSchema):
    """供应商响应"""
    id: int
    supplier_code: str
    supplier_name: str
    supplier_short_name: Optional[str] = None
    supplier_type: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    quality_rating: Optional[Decimal] = Decimal("0")
    delivery_rating: Optional[Decimal] = Decimal("0")
    service_rating: Optional[Decimal] = Decimal("0")
    overall_rating: Optional[Decimal] = Decimal("0")
    supplier_level: Optional[str] = "B"
    status: Optional[str] = "ACTIVE"
    cooperation_start: Optional[date] = None
    last_order_date: Optional[date] = None


# ==================== BOM ====================

class BomItemCreate(BaseModel):
    """BOM明细创建"""
    material_id: Optional[int] = None
    material_code: str = Field(max_length=50)
    material_name: str = Field(max_length=200)
    specification: Optional[str] = None
    drawing_no: Optional[str] = None
    unit: str = Field(default="件")
    quantity: Decimal = Field(gt=0, description="数量")
    unit_price: Optional[Decimal] = Field(default=0)
    source_type: str = Field(default="PURCHASE")
    supplier_id: Optional[int] = None
    required_date: Optional[date] = None
    is_key_item: bool = False
    remark: Optional[str] = None


class BomCreate(BaseModel):
    """创建BOM"""
    bom_no: str = Field(max_length=50)
    bom_name: str = Field(max_length=200)
    project_id: int
    machine_id: Optional[int] = None
    version: str = Field(default="1.0")
    items: List[BomItemCreate] = []
    remark: Optional[str] = None


class BomUpdate(BaseModel):
    """更新BOM"""
    bom_name: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class BomItemResponse(BaseSchema):
    """BOM明细响应"""
    id: int
    item_no: int
    material_id: Optional[int] = None
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    quantity: Decimal
    unit_price: Optional[Decimal] = 0
    amount: Optional[Decimal] = 0
    source_type: Optional[str] = None
    required_date: Optional[date] = None
    purchased_qty: Optional[Decimal] = 0
    received_qty: Optional[Decimal] = 0
    is_key_item: Optional[bool] = False


class BomResponse(TimestampSchema):
    """BOM响应"""
    id: int
    bom_no: str
    bom_name: str
    project_id: int
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    version: Optional[str] = "1.0"
    is_latest: Optional[bool] = True
    status: Optional[str] = "DRAFT"
    total_items: Optional[int] = 0
    total_amount: Optional[Decimal] = 0
    items: List[BomItemResponse] = []
