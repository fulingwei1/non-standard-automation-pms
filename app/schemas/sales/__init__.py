# -*- coding: utf-8 -*-
"""
销售管理 Schema 模块
"""

from .assessments import (
    FailureCaseCreate,
    FailureCaseResponse,
    OpenItemCreate,
    OpenItemResponse,
    ScoringRuleCreate,
    ScoringRuleResponse,
    TechnicalAssessmentApplyRequest,
    TechnicalAssessmentEvaluateRequest,
    TechnicalAssessmentResponse,
)
from .contracts import (
    ApprovalActionRequest,
    ApprovalHistoryResponse,
    ApprovalRecordResponse,
    ApprovalStartRequest,
    ApprovalStatusResponse,
    ContractAmendmentCreate,
    ContractAmendmentResponse,
    ContractCreate,
    ContractDeliverableCreate,
    ContractDeliverableResponse,
    ContractProjectCreateRequest,
    ContractResponse,
    ContractSignRequest,
    ContractUpdate,
)
from .cost_templates import (
    MaterialCostMatchRequest,
    MaterialCostMatchResponse,
    MaterialCostUpdateReminderResponse,
    MaterialCostUpdateReminderUpdate,
    PurchaseMaterialCostCreate,
    PurchaseMaterialCostResponse,
    PurchaseMaterialCostUpdate,
    QuoteCostTemplateCreate,
    QuoteCostTemplateResponse,
    QuoteCostTemplateUpdate,
)
from .invoices import (
    InvoiceApprovalCreate,
    InvoiceApprovalResponse,
    InvoiceCreate,
    InvoiceIssueRequest,
    InvoiceResponse,
    InvoiceUpdate,
)
from .leads import (
    LeadCreate,
    LeadFollowUpCreate,
    LeadFollowUpResponse,
    LeadResponse,
    LeadUpdate,
)
from .opportunities import (
    OpportunityCreate,
    OpportunityRequirementCreate,
    OpportunityRequirementResponse,
    OpportunityResponse,
    OpportunityUpdate,
)
from .quotes import (
    GateSubmitRequest,
    QuoteApproveRequest,
    QuoteCreate,
    QuoteItemBatchUpdate,
    QuoteItemCreate,
    QuoteItemResponse,
    QuoteItemUpdate,
    QuoteResponse,
    QuoteUpdate,
    QuoteVersionCreate,
    QuoteVersionResponse,
)

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
    # 审批工作流相关
    "ApprovalStartRequest", "ApprovalActionRequest", "ApprovalStatusResponse",
    "ApprovalRecordResponse", "ApprovalHistoryResponse",

    # 成本模板相关
    "QuoteCostTemplateCreate", "QuoteCostTemplateUpdate", "QuoteCostTemplateResponse",
    "PurchaseMaterialCostCreate", "PurchaseMaterialCostUpdate", "PurchaseMaterialCostResponse",
    "MaterialCostMatchRequest", "MaterialCostMatchResponse",
    "MaterialCostUpdateReminderResponse", "MaterialCostUpdateReminderUpdate",

    # 发票相关
    "InvoiceCreate", "InvoiceUpdate", "InvoiceResponse", "InvoiceIssueRequest",
    "InvoiceApprovalCreate", "InvoiceApprovalResponse",

    # 技术评估相关
    "TechnicalAssessmentApplyRequest", "TechnicalAssessmentEvaluateRequest", "TechnicalAssessmentResponse",
    "ScoringRuleCreate", "ScoringRuleResponse",
    "FailureCaseCreate", "FailureCaseResponse",
    "OpenItemCreate", "OpenItemResponse",
]
