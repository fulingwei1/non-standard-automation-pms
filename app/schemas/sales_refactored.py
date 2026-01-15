# -*- coding: utf-8 -*-
"""
销售管理模块 Schema (重构版)

模块化拆分后的统一导入
"""

# 从模块化文件导入所有Schema
from .leads import (
    LeadCreate, LeadUpdate, LeadResponse,
    LeadFollowUpCreate, LeadFollowUpResponse
)

from .opportunities import (
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    OpportunityRequirementCreate, OpportunityRequirementResponse
)

from .quotes import (
    QuoteCreate, QuoteUpdate, QuoteResponse,
    QuoteItemCreate, QuoteItemUpdate, QuoteItemResponse,
    QuoteItemBatchUpdate, QuoteVersionCreate, QuoteVersionResponse,
    GateSubmitRequest, QuoteApproveRequest
)

from .contracts import (
    ContractCreate, ContractUpdate, ContractResponse,
    ContractDeliverableCreate, ContractDeliverableResponse,
    ContractAmendmentCreate, ContractAmendmentResponse,
    ContractSignRequest, ContractProjectCreateRequest
)

# 其他未拆分的Schema（发票、应收款、审批等）
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from .common import BaseSchema, TimestampSchema


class InvoiceCreate(BaseModel):
    """创建发票"""
    model_config = ConfigDict(populate_by_name=True)
    
    contract_id: int = Field(description="合同ID")
    invoice_code: Optional[str] = Field(default=None, max_length=20, description="发票编码")
    invoice_type: Optional[str] = Field(default=None, description="发票类型")
    invoice_amount: Decimal = Field(gt=0, description="发票金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    invoice_date: Optional[date] = Field(default=None, description="开票日期")
    due_date: Optional[date] = Field(default=None, description="到期日期")
    remark: Optional[str] = Field(default=None, description="备注")


class InvoiceUpdate(BaseModel):
    """更新发票"""
    
    invoice_code: Optional[str] = None
    invoice_type: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    remark: Optional[str] = None


class InvoiceResponse(TimestampSchema):
    """发票响应"""
    
    id: int = Field(description="发票ID")
    contract_id: int = Field(description="合同ID")
    invoice_code: str = Field(description="发票编码")
    invoice_type: Optional[str] = Field(default=None, description="发票类型")
    invoice_amount: Decimal = Field(description="发票金额")
    tax_rate: Optional[Decimal] = Field(default=None, description="税率")
    tax_amount: Optional[Decimal] = Field(default=None, description="税额")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    invoice_date: Optional[date] = Field(default=None, description="开票日期")
    due_date: Optional[date] = Field(default=None, description="到期日期")
    remark: Optional[str] = Field(default=None, description="备注")
    contract_code: Optional[str] = Field(default=None, description="合同编码")


# 为了向后兼容，导出所有类
__all__ = [
    # 线索相关
    "LeadCreate", "LeadUpdate", "LeadResponse",
    "LeadFollowUpCreate", "LeadFollowUpResponse",
    
    # 机会相关
    "OpportunityCreate", "OpportunityUpdate", "OpportunityResponse",
    "OpportunityRequirementCreate", "OpportunityRequirementResponse",
    
    # 报价相关
    "QuoteCreate", "QuoteUpdate", "QuoteResponse",
    "QuoteItemCreate", "QuoteItemUpdate", "QuoteItemResponse",
    "QuoteItemBatchUpdate", "QuoteVersionCreate", "QuoteVersionResponse",
    "GateSubmitRequest", "QuoteApproveRequest",
    
    # 合同相关
    "ContractCreate", "ContractUpdate", "ContractResponse",
    "ContractDeliverableCreate", "ContractDeliverableResponse",
    "ContractAmendmentCreate", "ContractAmendmentResponse",
    "ContractSignRequest", "ContractProjectCreateRequest",
    
    # 发票相关
    "InvoiceCreate", "InvoiceUpdate", "InvoiceResponse",
]