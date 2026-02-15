"""
AI报价单自动生成Schemas
Team 5: AI Quotation Generator Schemas
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


class QuotationType(str, Enum):
    """报价单类型"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class QuotationStatus(str, Enum):
    """报价单状态"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# ============= 报价项相关 =============

class QuotationItem(BaseModel):
    """报价项"""
    item_id: Optional[int] = Field(None, description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    quantity: Decimal = Field(..., description="数量", ge=0)
    unit: str = Field(..., description="单位")
    unit_price: Decimal = Field(..., description="单价", ge=0)
    total_price: Decimal = Field(..., description="总价", ge=0)
    category: Optional[str] = Field(None, description="类别")
    
    @validator('total_price', always=True)
    def calculate_total(cls, v, values):
        """自动计算总价"""
        if 'quantity' in values and 'unit_price' in values:
            return values['quantity'] * values['unit_price']
        return v


# ============= 请求相关 =============

class QuotationGenerateRequest(BaseModel):
    """生成报价单请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    customer_id: Optional[int] = Field(None, description="客户ID")
    quotation_type: QuotationType = Field(QuotationType.STANDARD, description="报价单类型")
    items: List[QuotationItem] = Field(..., description="报价项清单")
    tax_rate: Optional[Decimal] = Field(Decimal("0.13"), description="税率", ge=0, le=1)
    discount_rate: Optional[Decimal] = Field(Decimal("0"), description="折扣率", ge=0, le=1)
    validity_days: Optional[int] = Field(30, description="有效期（天）", ge=1)
    payment_terms: Optional[str] = Field(None, description="付款条款")
    notes: Optional[str] = Field(None, description="备注")
    
    class Config:
        json_schema_extra = {
            "example": {
                "presale_ticket_id": 1,
                "customer_id": 1,
                "quotation_type": "standard",
                "items": [
                    {
                        "name": "定制化ERP系统开发",
                        "description": "包含库存管理、财务管理、人力资源等模块",
                        "quantity": 1,
                        "unit": "套",
                        "unit_price": 150000,
                        "category": "软件开发"
                    }
                ],
                "tax_rate": 0.13,
                "discount_rate": 0.05,
                "validity_days": 30,
                "payment_terms": "首付30%，中期验收30%，终期验收40%"
            }
        }


class ThreeTierQuotationRequest(BaseModel):
    """生成三档报价方案请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    customer_id: Optional[int] = Field(None, description="客户ID")
    base_requirements: str = Field(..., description="基础需求描述")
    budget_range: Optional[Dict[str, Decimal]] = Field(None, description="预算范围")
    priority_features: Optional[List[str]] = Field(None, description="优先功能列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "presale_ticket_id": 1,
                "customer_id": 1,
                "base_requirements": "企业需要一套ERP系统，包含基本的进销存和财务管理功能",
                "budget_range": {"min": 50000, "max": 200000},
                "priority_features": ["库存管理", "财务管理", "报表分析"]
            }
        }


class QuotationUpdateRequest(BaseModel):
    """更新报价单请求"""
    items: Optional[List[QuotationItem]] = Field(None, description="报价项清单")
    tax_rate: Optional[Decimal] = Field(None, description="税率", ge=0, le=1)
    discount_rate: Optional[Decimal] = Field(None, description="折扣率", ge=0, le=1)
    validity_days: Optional[int] = Field(None, description="有效期（天）", ge=1)
    payment_terms: Optional[str] = Field(None, description="付款条款")
    status: Optional[QuotationStatus] = Field(None, description="状态")
    notes: Optional[str] = Field(None, description="备注")


class QuotationApprovalRequest(BaseModel):
    """审批报价单请求"""
    status: str = Field(..., description="审批状态 (approved/rejected)")
    comments: Optional[str] = Field(None, description="审批意见")
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['approved', 'rejected']:
            raise ValueError('status must be approved or rejected')
        return v


class QuotationEmailRequest(BaseModel):
    """发送报价单邮件请求"""
    to_email: str = Field(..., description="收件人邮箱")
    cc_emails: Optional[List[str]] = Field(None, description="抄送邮箱列表")
    subject: Optional[str] = Field(None, description="邮件主题")
    message: Optional[str] = Field(None, description="邮件正文")
    include_pdf: bool = Field(True, description="是否包含PDF附件")


# ============= 响应相关 =============

class QuotationItemResponse(BaseModel):
    """报价项响应"""
    item_id: Optional[int]
    name: str
    description: Optional[str]
    quantity: Decimal
    unit: str
    unit_price: Decimal
    total_price: Decimal
    category: Optional[str]
    
    class Config:
        from_attributes = True


class QuotationResponse(BaseModel):
    """报价单响应"""
    id: int
    presale_ticket_id: int
    customer_id: Optional[int]
    quotation_number: str
    quotation_type: QuotationType
    items: List[Dict[str, Any]]
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
    payment_terms: Optional[str]
    validity_days: int
    status: QuotationStatus
    pdf_url: Optional[str]
    version: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    ai_model: Optional[str]
    generation_time: Optional[Decimal]
    notes: Optional[str]
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class ThreeTierQuotationResponse(BaseModel):
    """三档报价方案响应"""
    basic: QuotationResponse
    standard: QuotationResponse
    premium: QuotationResponse
    recommendation: str = Field(..., description="推荐方案")
    comparison: Dict[str, Any] = Field(..., description="方案对比")


class QuotationVersionResponse(BaseModel):
    """报价单版本响应"""
    id: int
    quotation_id: int
    version: int
    snapshot_data: Dict[str, Any]
    changed_by: int
    change_summary: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuotationHistoryResponse(BaseModel):
    """报价单历史响应"""
    quotation_id: int
    current_version: int
    versions: List[QuotationVersionResponse]
    total_versions: int


class QuotationApprovalResponse(BaseModel):
    """审批响应"""
    id: int
    quotation_id: int
    approver_id: int
    status: str
    comments: Optional[str]
    created_at: datetime
    approved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============= 模板相关 =============

class QuotationTemplateResponse(BaseModel):
    """报价单模板响应"""
    id: int
    name: str
    template_type: str
    template_content: Dict[str, Any]
    pdf_template_path: Optional[str]
    default_validity_days: int
    default_tax_rate: Decimal
    default_discount_rate: Decimal
    is_active: bool
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
