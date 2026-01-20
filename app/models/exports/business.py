"""
业务模型导出模块

包含：
- 销售管理（线索、商机、报价、合同）
- 售前支持
- 报价管理
"""

# 销售管理
from ..sales import (
    AIClarification,
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    Contract,
    ContractAmendment,
    ContractApproval,
    ContractTemplate,
    CpqRuleSet,
    Lead,
    LeadAssessment,
    LeadFollowUp,
    MaterialCostUpdateReminder,
    Opportunity,
    OpportunityRequirement,
    PurchaseMaterialCost,
    Quote,
    QuoteCostApproval,
    QuoteCostHistory,
    QuoteCostTemplate,
    QuoteItem,
    QuoteTemplate,
    QuoteTemplateVersion,
    QuoteVersion,
    SalesOrder,
    TechnicalAssessment,
)

# 售前支持
from ..presale import (
    PresaleSolution,
    PresaleSolutionCost,
    PresaleSolutionTemplate,
    PresaleSupportTicket,
    PresaleTicketDeliverable,
    PresaleTicketProgress,
    PresaleWorkload,
)

__all__ = [
    # 销售
    "Lead",
    "LeadFollowUp",
    "LeadAssessment",
    "Opportunity",
    "OpportunityRequirement",
    "Quote",
    "QuoteVersion",
    "QuoteItem",
    "QuoteCostTemplate",
    "QuoteCostApproval",
    "QuoteCostHistory",
    "PurchaseMaterialCost",
    "MaterialCostUpdateReminder",
    "CpqRuleSet",
    "QuoteTemplate",
    "QuoteTemplateVersion",
    "Contract",
    "ContractTemplate",
    "ContractAmendment",
    "ContractApproval",
    "SalesOrder",
    "TechnicalAssessment",
    "AIClarification",
    "ApprovalWorkflow",
    "ApprovalWorkflowStep",
    "ApprovalHistory",
    "ApprovalRecord",
    # 售前
    "PresaleSupportTicket",
    "PresaleTicketDeliverable",
    "PresaleTicketProgress",
    "PresaleSolution",
    "PresaleSolutionCost",
    "PresaleSolutionTemplate",
    "PresaleWorkload",
]
