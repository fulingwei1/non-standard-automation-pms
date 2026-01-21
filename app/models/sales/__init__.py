# -*- coding: utf-8 -*-
"""
销售管理模块 - 模型聚合
"""

# 合同相关
from .contracts import (
    Contract,
    ContractAmendment,
    ContractApproval,
    ContractDeliverable,
    ContractTemplate,
    ContractTemplateVersion,
)

# 发票相关
from .invoices import (
    Invoice,
    InvoiceApproval,
    ReceivableDispute,
)

# 线索和商机
from .leads import (
    Lead,
    LeadFollowUp,
    Opportunity,
    OpportunityRequirement,
)

# 报价相关
from .quotes import (
    CpqRuleSet,
    MaterialCostUpdateReminder,
    PurchaseMaterialCost,
    Quote,
    QuoteCostApproval,
    QuoteCostHistory,
    QuoteCostTemplate,
    QuoteItem,
    QuoteTemplate,
    QuoteTemplateVersion,
    QuoteVersion,
)

# 技术评估和需求
from .technical_assessment import (
    AIClarification,
    FailureCase,
    LeadRequirementDetail,
    OpenItem,
    QuoteApproval,
    RequirementFreeze,
    ScoringRule,
    TechnicalAssessment,
)

# 审批工作流和目标
from .workflow import (
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    SalesRankingConfig,
    SalesTarget,
)

# 团队管理
from .team import (
    SalesTeam,
    SalesTeamMember,
    TeamPerformanceSnapshot,
    TeamPKRecord,
)

__all__ = [
    # 线索和商机
    "Lead",
    "LeadFollowUp",
    "Opportunity",
    "OpportunityRequirement",
    # 报价相关
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
    # 合同相关
    "ContractTemplate",
    "ContractTemplateVersion",
    "Contract",
    "ContractDeliverable",
    "ContractAmendment",
    "ContractApproval",
    # 发票相关
    "Invoice",
    "ReceivableDispute",
    "InvoiceApproval",
    # 技术评估和需求
    "TechnicalAssessment",
    "ScoringRule",
    "FailureCase",
    "LeadRequirementDetail",
    "RequirementFreeze",
    "OpenItem",
    "AIClarification",
    "QuoteApproval",
    # 审批工作流和目标
    "ApprovalWorkflow",
    "ApprovalWorkflowStep",
    "ApprovalRecord",
    "ApprovalHistory",
    "SalesTarget",
    "SalesRankingConfig",
    # 团队管理
    "SalesTeam",
    "SalesTeamMember",
    "TeamPerformanceSnapshot",
    "TeamPKRecord",
]
