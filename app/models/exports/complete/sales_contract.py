# -*- coding: utf-8 -*-
"""
完整模型导出 - 销售和合同相关
"""
# AI方案生成
from ...presale_ai_solution import (
    PresaleAIGenerationLog,
    PresaleAISolution,
)

# 销售管理
from ...sales import (
    AIClarification,
    Contract,
    ContractAmendment,
    ContractDeliverable,
    ContractTemplate,
    ContractTemplateVersion,
    CpqRuleSet,
    FailureCase,
    Invoice,
    Lead,
    LeadFollowUp,
    LeadRequirementDetail,
    MaterialCostUpdateReminder,
    OpenItem,
    Opportunity,
    OpportunityRequirement,
    PurchaseMaterialCost,
    Quote,
    QuoteCostTemplate,
    QuoteItem,
    QuoteTemplate,
    QuoteTemplateVersion,
    QuoteVersion,
    ReceivableDispute,
    RequirementFreeze,
    SalesTarget,
    ScoringRule,
    TechnicalAssessment,
    # 评估模板和工作流（2026-03-12 新增）
    AssessmentTemplate,
    AssessmentItem,
    AssessmentRisk,
    AssessmentVersion,
    # 销售漏斗状态机（2026-03-12 新增）
    SalesFunnelStage,
    StageGateConfig,
    StageGateResult,
    StageDwellTimeConfig,
    StageDwellTimeAlert,
    FunnelTransitionLog,
    FunnelSnapshot,
)

__all__ = [
    # Sales
    "Lead",
    "LeadFollowUp",
    "Opportunity",
    "OpportunityRequirement",
    "Quote",
    "QuoteVersion",
    "QuoteItem",
    "QuoteCostTemplate",
    "PurchaseMaterialCost",
    "MaterialCostUpdateReminder",
    "CpqRuleSet",
    "QuoteTemplate",
    "QuoteTemplateVersion",
    "ContractTemplate",
    "ContractTemplateVersion",
    "Contract",
    "ContractDeliverable",
    "ContractAmendment",
    "Invoice",
    "ReceivableDispute",
    "SalesTarget",
    # Technical Assessment
    "TechnicalAssessment",
    "ScoringRule",
    "FailureCase",
    "LeadRequirementDetail",
    "RequirementFreeze",
    "OpenItem",
    "AIClarification",
    # AI Solution Generation
    "PresaleAISolution",
    "PresaleAIGenerationLog",
    # Assessment Template & Workflow
    "AssessmentTemplate",
    "AssessmentItem",
    "AssessmentRisk",
    "AssessmentVersion",
    # Sales Funnel State Machine
    "SalesFunnelStage",
    "StageGateConfig",
    "StageGateResult",
    "StageDwellTimeConfig",
    "StageDwellTimeAlert",
    "FunnelTransitionLog",
    "FunnelSnapshot",
]
