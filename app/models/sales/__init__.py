# -*- coding: utf-8 -*-
"""
销售管理模块 - 模型聚合
"""

# 客户和联系人（Customer在project模块中定义）
from ..project.customer import Customer
from .contacts import Contact
from .customer_tags import CustomerTag, PredefinedTags

# 合同相关
from .contracts import (
    Contract,
    ContractAmendment,
    ContractApproval,
    ContractAttachment,
    ContractDeliverable,
    ContractTemplate,
    ContractTemplateVersion,
    ContractTerm,
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

# 销售目标 V2
from .target_v2 import (
    SalesTargetV2,
    TargetBreakdownLog,
    TargetPeriodEnumV2,
    TargetTypeEnumV2,
)

# 销售区域
from .region import SalesRegion

# AI赢率预测
from .presale_ai_win_rate import (
    PresaleAIWinRate,
    PresaleWinRateHistory,
    WinRateResultEnum,
)

# AI成本估算
from .presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory,
    PresaleCostOptimizationRecord,
)

__all__ = [
    # 客户和联系人
    "Customer",
    "Contact",
    "CustomerTag",
    "PredefinedTags",
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
    "ContractTerm",
    "ContractAttachment",
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
    # 销售目标 V2
    "SalesTargetV2",
    "TargetBreakdownLog",
    "TargetPeriodEnumV2",
    "TargetTypeEnumV2",
    # 销售区域
    "SalesRegion",
    # AI赢率预测
    "PresaleAIWinRate",
    "PresaleWinRateHistory",
    "WinRateResultEnum",
    # AI成本估算
    "PresaleAICostEstimation",
    "PresaleCostHistory",
    "PresaleCostOptimizationRecord",
]
