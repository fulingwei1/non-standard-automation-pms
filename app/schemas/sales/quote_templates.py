# -*- coding: utf-8 -*-
"""
报价模板与CPQ规则集 Schema

定义报价模板、版本和CPQ规则集的请求/响应模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== CPQ 规则集 ====================


class CpqRuleSetBase(BaseModel):
    """CPQ规则集基础模型"""

    rule_code: str = Field(..., max_length=50, description="规则集编码")
    rule_name: str = Field(..., max_length=200, description="规则集名称")
    description: Optional[str] = Field(None, description="描述")
    base_price: Decimal = Field(Decimal("0"), description="基准价格")
    currency: str = Field("CNY", max_length=10, description="币种")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置项定义")
    pricing_matrix: Optional[Dict[str, Any]] = Field(None, description="价格矩阵")
    approval_threshold: Optional[Dict[str, Any]] = Field(None, description="审批阈值配置")
    visibility_scope: str = Field("ALL", description="可见范围")
    is_default: bool = Field(False, description="是否默认")
    owner_role: Optional[str] = Field(None, max_length=50, description="负责角色")


class CpqRuleSetCreate(CpqRuleSetBase):
    """创建CPQ规则集"""

    pass


class CpqRuleSetUpdate(BaseModel):
    """更新CPQ规则集"""

    rule_name: Optional[str] = Field(None, max_length=200, description="规则集名称")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[str] = Field(None, description="状态")
    base_price: Optional[Decimal] = Field(None, description="基准价格")
    currency: Optional[str] = Field(None, max_length=10, description="币种")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置项定义")
    pricing_matrix: Optional[Dict[str, Any]] = Field(None, description="价格矩阵")
    approval_threshold: Optional[Dict[str, Any]] = Field(None, description="审批阈值配置")
    visibility_scope: Optional[str] = Field(None, description="可见范围")
    is_default: Optional[bool] = Field(None, description="是否默认")
    owner_role: Optional[str] = Field(None, max_length=50, description="负责角色")


class CpqRuleSetResponse(CpqRuleSetBase):
    """CPQ规则集响应"""

    id: int
    status: str = Field("ACTIVE", description="状态")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==================== 报价模板版本 ====================


class QuoteTemplateVersionBase(BaseModel):
    """报价模板版本基础模型"""

    version_no: str = Field(..., description="版本号")
    sections: Optional[Dict[str, Any]] = Field(None, description="模板结构配置")
    pricing_rules: Optional[Dict[str, Any]] = Field(None, description="价格规则")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置项定义")
    discount_rules: Optional[Dict[str, Any]] = Field(None, description="折扣规则")
    release_notes: Optional[str] = Field(None, description="版本说明")
    rule_set_id: Optional[int] = Field(None, description="关联规则集ID")


class QuoteTemplateVersionCreate(QuoteTemplateVersionBase):
    """创建报价模板版本"""

    pass


class QuoteTemplateVersionResponse(QuoteTemplateVersionBase):
    """报价模板版本响应"""

    id: int
    template_id: int
    status: str = Field("DRAFT", description="状态")
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    published_by: Optional[int] = None
    publisher_name: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==================== 报价模板 ====================


class QuoteTemplateBase(BaseModel):
    """报价模板基础模型"""

    template_code: str = Field(..., max_length=50, description="模板编码")
    template_name: str = Field(..., max_length=200, description="模板名称")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    description: Optional[str] = Field(None, description="描述")
    visibility_scope: str = Field("TEAM", description="可见范围")
    is_default: bool = Field(False, description="是否默认模板")


class QuoteTemplateCreate(QuoteTemplateBase):
    """创建报价模板"""

    initial_version: Optional[QuoteTemplateVersionCreate] = Field(
        None, description="初始版本（可选）"
    )


class QuoteTemplateUpdate(BaseModel):
    """更新报价模板"""

    template_name: Optional[str] = Field(None, max_length=200, description="模板名称")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    description: Optional[str] = Field(None, description="描述")
    visibility_scope: Optional[str] = Field(None, description="可见范围")
    is_default: Optional[bool] = Field(None, description="是否默认模板")
    status: Optional[str] = Field(None, description="状态")


class QuoteTemplateResponse(QuoteTemplateBase):
    """报价模板响应"""

    id: int
    status: str = Field("DRAFT", description="状态")
    current_version_id: Optional[int] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    current_version: Optional[QuoteTemplateVersionResponse] = None
    versions: List[QuoteTemplateVersionResponse] = Field(default_factory=list)
    version_count: int = Field(0, description="版本数量")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==================== 通用模板工具 ====================


class TemplateVersionDiff(BaseModel):
    """模板版本差异"""

    sections: Dict[str, Any] = Field(default_factory=dict, description="结构差异")
    pricing_rules: Dict[str, Any] = Field(default_factory=dict, description="价格规则差异")
    clause_sections: Dict[str, Any] = Field(default_factory=dict, description="条款差异")


class TemplateApprovalHistoryRecord(BaseModel):
    """模板审批历史记录"""

    version_id: int
    version_no: str
    status: str
    published_by: Optional[int] = None
    publisher_name: Optional[str] = None
    published_at: Optional[datetime] = None
    release_notes: Optional[str] = None


# ==================== 报价模板应用 ====================


class QuoteTemplateApplyRequest(BaseModel):
    """应用报价模板请求"""

    template_id: int = Field(..., description="模板ID")
    version_id: Optional[int] = Field(None, description="版本ID")
    quote_id: Optional[int] = Field(None, description="目标报价ID")
    opportunity_id: Optional[int] = Field(None, description="商机ID")
    customizations: Optional[Dict[str, Any]] = Field(None, description="自定义参数")


class QuoteTemplateApplyResponse(BaseModel):
    """应用报价模板响应"""

    success: bool
    quote_id: Optional[int] = None
    quote_code: Optional[str] = None
    template_id: int
    version_id: int
    applied_sections: Optional[List[str]] = None
    message: Optional[str] = None


# ==================== CPQ 价格预览 ====================


class CpqPricePreviewRequest(BaseModel):
    """CPQ价格预览请求"""

    rule_set_id: int = Field(..., description="规则集ID")
    config_values: Dict[str, Any] = Field(..., description="配置值")
    quantity: int = Field(1, ge=1, description="数量")
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="折扣率")


class CpqPricePreviewResponse(BaseModel):
    """CPQ价格预览响应"""

    rule_set_id: int
    rule_name: str
    base_price: Decimal
    config_adjustments: Dict[str, Decimal] = Field(default_factory=dict, description="配置调整金额")
    quantity: int
    subtotal: Decimal = Field(..., description="小计")
    discount_rate: Optional[Decimal] = None
    discount_amount: Decimal = Field(Decimal("0"), description="折扣金额")
    final_price: Decimal = Field(..., description="最终价格")
    currency: str = Field("CNY", description="币种")
    breakdown: Optional[List[Dict[str, Any]]] = Field(None, description="价格明细")
