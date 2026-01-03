# -*- coding: utf-8 -*-
"""
物料管理 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal

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
    level: int = 1
    full_path: Optional[str] = None
    is_active: bool = True
    children: List['MaterialCategoryResponse'] = []


# ==================== 物料 ====================

class MaterialCreate(BaseModel):
    """创建物料"""
    material_code: str = Field(max_length=50, description="物料编码")
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
    material_code: str
    material_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    unit: str = "件"
    material_type: Optional[str] = None
    source_type: str = "PURCHASE"
    standard_price: Decimal = 0
    last_price: Decimal = 0
    safety_stock: Decimal = 0
    current_stock: Decimal = 0
    lead_time_days: int = 0
    is_key_material: bool = False
    is_active: bool = True


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
    quality_rating: Decimal = 0
    delivery_rating: Decimal = 0
    overall_rating: Decimal = 0
    supplier_level: str = "B"
    status: str = "ACTIVE"


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
    material_code: str
    material_name: str
    specification: Optional[str] = None
    unit: str
    quantity: Decimal
    unit_price: Decimal = 0
    amount: Decimal = 0
    source_type: str
    required_date: Optional[date] = None
    purchased_qty: Decimal = 0
    received_qty: Decimal = 0
    is_key_item: bool = False


class BomResponse(TimestampSchema):
    """BOM响应"""
    id: int
    bom_no: str
    bom_name: str
    project_id: int
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    version: str = "1.0"
    is_latest: bool = True
    status: str = "DRAFT"
    total_items: int = 0
    total_amount: Decimal = 0
    items: List[BomItemResponse] = []
