# -*- coding: utf-8 -*-
"""
销售管理 Schema 模块
"""

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

# 简单导出，避免循环依赖
__all__ = []

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
]