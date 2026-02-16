# -*- coding: utf-8 -*-
"""
智能采购管理 - Pydantic Schemas
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


# ==================== 采购建议 ====================

class PurchaseSuggestionBase(BaseModel):
    """采购建议基础模型"""
    material_id: int
    suggested_qty: Decimal = Field(..., gt=0, description="建议数量")
    source_type: str = Field(..., description="来源类型：SHORTAGE/SAFETY_STOCK/FORECAST/MANUAL")
    source_id: Optional[int] = None
    project_id: Optional[int] = None
    required_date: Optional[date] = None
    urgency_level: str = Field(default="NORMAL", description="紧急程度")
    remark: Optional[str] = None


class PurchaseSuggestionCreate(PurchaseSuggestionBase):
    """创建采购建议"""
    pass


class PurchaseSuggestionUpdate(BaseModel):
    """更新采购建议"""
    suggested_qty: Optional[Decimal] = None
    required_date: Optional[date] = None
    urgency_level: Optional[str] = None
    suggested_supplier_id: Optional[int] = None
    estimated_unit_price: Optional[Decimal] = None
    remark: Optional[str] = None


class PurchaseSuggestionApprove(BaseModel):
    """审批采购建议"""
    approved: bool = Field(..., description="是否批准")
    review_note: Optional[str] = None
    suggested_supplier_id: Optional[int] = None


class PurchaseSuggestionResponse(PurchaseSuggestionBase):
    """采购建议响应"""
    id: int
    suggestion_no: str
    material_code: str
    material_name: str
    specification: Optional[str]
    unit: str
    current_stock: Decimal
    safety_stock: Decimal
    suggested_supplier_id: Optional[int]
    suggested_supplier_name: Optional[str] = None
    ai_confidence: Optional[Decimal]
    recommendation_reason: Optional[Dict[str, Any]]
    alternative_suppliers: Optional[List[Dict[str, Any]]]
    estimated_unit_price: Optional[Decimal]
    estimated_total_amount: Optional[Decimal]
    status: str
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    review_note: Optional[str]
    purchase_order_id: Optional[int]
    purchase_order_no: Optional[str] = None
    ordered_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 供应商报价 ====================

class SupplierQuotationBase(BaseModel):
    """供应商报价基础模型"""
    supplier_id: int
    material_id: int
    unit_price: Decimal = Field(..., gt=0, description="单价")
    currency: str = Field(default="CNY")
    min_order_qty: Decimal = Field(default=1, gt=0)
    lead_time_days: int = Field(default=0, ge=0, description="交货周期")
    valid_from: date
    valid_to: date
    payment_terms: Optional[str] = None
    warranty_period: Optional[str] = None
    tax_rate: Decimal = Field(default=13, ge=0, le=100)
    remark: Optional[str] = None

    @validator('valid_to')
    def validate_dates(cls, v, values):
        if 'valid_from' in values and v < values['valid_from']:
            raise ValueError('有效期止日期必须大于等于有效期起日期')
        return v


class SupplierQuotationCreate(SupplierQuotationBase):
    """创建供应商报价"""
    pass


class SupplierQuotationUpdate(BaseModel):
    """更新供应商报价"""
    unit_price: Optional[Decimal] = None
    min_order_qty: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    payment_terms: Optional[str] = None
    warranty_period: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class SupplierQuotationResponse(SupplierQuotationBase):
    """供应商报价响应"""
    id: int
    quotation_no: str
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    material_code: str
    material_name: str
    specification: Optional[str]
    status: str
    is_selected: bool
    inquiry_id: Optional[int]
    attachments: Optional[List[Dict[str, Any]]]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuotationCompareRequest(BaseModel):
    """报价比较请求"""
    material_id: int
    supplier_ids: Optional[List[int]] = None


class QuotationCompareItem(BaseModel):
    """报价比较项"""
    quotation_id: int
    quotation_no: str
    supplier_id: int
    supplier_code: str
    supplier_name: str
    unit_price: Decimal
    currency: str
    min_order_qty: Decimal
    lead_time_days: int
    valid_from: date
    valid_to: date
    payment_terms: Optional[str]
    tax_rate: Decimal
    is_selected: bool
    performance_score: Optional[Decimal] = None
    performance_rating: Optional[str] = None


class QuotationCompareResponse(BaseModel):
    """报价比较响应"""
    material_id: int
    material_code: str
    material_name: str
    quotations: List[QuotationCompareItem]
    best_price_supplier_id: Optional[int] = None
    recommended_supplier_id: Optional[int] = None
    recommendation_reason: Optional[str] = None


# ==================== 供应商绩效 ====================

class SupplierPerformanceCalculate(BaseModel):
    """触发供应商绩效评估"""
    supplier_id: int
    evaluation_period: str = Field(..., description="评估期间 YYYY-MM")
    weight_config: Optional[Dict[str, Decimal]] = Field(
        default={
            "on_time_delivery": Decimal("30"),
            "quality": Decimal("30"),
            "price": Decimal("20"),
            "response": Decimal("20"),
        },
        description="评分权重配置（总和应为100）"
    )


class SupplierPerformanceResponse(BaseModel):
    """供应商绩效响应"""
    id: int
    supplier_id: int
    supplier_code: str
    supplier_name: str
    evaluation_period: str
    period_start: date
    period_end: date
    
    # 统计数据
    total_orders: int
    total_amount: Decimal
    
    # 各维度评分
    on_time_delivery_rate: Decimal
    on_time_orders: int
    late_orders: int
    avg_delay_days: Decimal
    
    quality_pass_rate: Decimal
    total_received_qty: Decimal
    qualified_qty: Decimal
    rejected_qty: Decimal
    
    price_competitiveness: Decimal
    avg_price_vs_market: Decimal
    
    response_speed_score: Decimal
    avg_response_hours: Decimal
    
    service_score: Optional[Decimal]
    
    # 综合评分
    overall_score: Decimal
    rating: Optional[str]
    
    weight_config: Optional[Dict[str, Any]]
    detail_data: Optional[Dict[str, Any]]
    status: str
    
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    review_note: Optional[str]
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierRankingItem(BaseModel):
    """供应商排名项"""
    supplier_id: int
    supplier_code: str
    supplier_name: str
    overall_score: Decimal
    rating: Optional[str]
    on_time_delivery_rate: Decimal
    quality_pass_rate: Decimal
    price_competitiveness: Decimal
    response_speed_score: Decimal
    total_orders: int
    total_amount: Decimal
    evaluation_period: str
    rank: int


class SupplierRankingResponse(BaseModel):
    """供应商排名响应"""
    evaluation_period: str
    total_suppliers: int
    rankings: List[SupplierRankingItem]


# ==================== 采购订单跟踪 ====================

class PurchaseOrderTrackingCreate(BaseModel):
    """创建订单跟踪记录"""
    order_id: int
    event_type: str = Field(..., description="事件类型")
    event_description: Optional[str] = None
    tracking_no: Optional[str] = None
    logistics_company: Optional[str] = None
    estimated_arrival: Optional[date] = None
    note: Optional[str] = None


class PurchaseOrderTrackingResponse(BaseModel):
    """订单跟踪响应"""
    id: int
    order_id: int
    order_no: str
    event_type: str
    event_time: datetime
    event_description: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    tracking_no: Optional[str]
    logistics_company: Optional[str]
    estimated_arrival: Optional[date]
    attachments: Optional[List[Dict[str, Any]]]
    note: Optional[str]
    operator_id: Optional[int]
    operator_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderReceiveRequest(BaseModel):
    """收货确认请求"""
    receipt_date: date = Field(default_factory=date.today)
    delivery_note_no: Optional[str] = None
    logistics_company: Optional[str] = None
    tracking_no: Optional[str] = None
    items: List[Dict[str, Any]] = Field(..., description="收货明细")
    remark: Optional[str] = None


# ==================== 建议转订单 ====================

class CreateOrderFromSuggestionRequest(BaseModel):
    """从建议创建订单请求"""
    supplier_id: Optional[int] = None
    required_date: Optional[date] = None
    payment_terms: Optional[str] = None
    delivery_address: Optional[str] = None
    remark: Optional[str] = None


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    total: int
    page: int
    page_size: int
    items: List[Any]
