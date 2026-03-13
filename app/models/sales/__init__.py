# -*- coding: utf-8 -*-
"""
销售管理模块 - 模型聚合
"""

# 客户和联系人（Customer在project模块中定义）
from ..project.customer import Customer
from .contacts import Contact

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
from .customer_tags import CustomerTag, PredefinedTags

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

# AI成本估算
from .presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory,
    PresaleCostOptimizationRecord,
)

# 方案版本
from .solution_version import SolutionVersion

# AI赢率预测
from .presale_ai_win_rate import (
    PresaleAIWinRate,
    PresaleWinRateHistory,
    WinRateResultEnum,
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

# 销售区域
from .region import SalesRegion

# 业务操作日志
from .operation_log import SalesEntityType, SalesOperationLog, SalesOperationType

# 数据审核流程
from .data_audit import (
    DataAuditPriorityEnum,
    DataAuditStatusEnum,
    DataChangeType,
    SalesDataAuditRequest,
)

# 客户关系成熟度评分
from .relationship_scores import CustomerRelationshipScore

# 销售目标 V2
from .target_v2 import (
    SalesTargetV2,
    TargetBreakdownLog,
    TargetPeriodEnumV2,
    TargetTypeEnumV2,
)

# 团队管理
from .team import (
    SalesTeam,
    SalesTeamMember,
    TeamPerformanceSnapshot,
    TeamPKRecord,
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

# 评估模板和工作流（2026-03-12 新增）
from .assessment_template import (
    AssessmentDimensionEnum,
    AssessmentItem,
    AssessmentRisk,
    AssessmentTemplate,
    AssessmentVersion,
    RiskLevelEnum,
    RiskStatusEnum,
    TemplateCategoryEnum,
)

# 销售漏斗状态机（2026-03-12 新增）
from .sales_funnel import (
    AlertSeverityEnum,
    AlertStatusEnum,
    FunnelEntityTypeEnum,
    FunnelSnapshot,
    FunnelTransitionLog,
    GateResultEnum,
    GateTypeEnum,
    SalesFunnelStage,
    StageDwellTimeAlert,
    StageDwellTimeConfig,
    StageGateConfig,
    StageGateResult,
)

# 线索需求详情 V2（拆分后的子表）
from .lead_requirement_v2 import (
    LeadRequirementBasicV2,
    LeadRequirementFacilityV2,
    LeadRequirementTechnicalV2,
)

# 毛利率预警
from .margin_alert import (
    MarginAlertConfig,
    MarginAlertLevelEnum,
    MarginAlertRecord,
    MarginAlertStatusEnum,
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
    # 方案版本
    "SolutionVersion",
    # 客户关系成熟度评分
    "CustomerRelationshipScore",
    # 业务操作日志
    "SalesOperationLog",
    "SalesOperationType",
    "SalesEntityType",
    # 数据审核流程
    "SalesDataAuditRequest",
    "DataAuditStatusEnum",
    "DataAuditPriorityEnum",
    "DataChangeType",
    # 线索需求详情 V2
    "LeadRequirementBasicV2",
    "LeadRequirementTechnicalV2",
    "LeadRequirementFacilityV2",
    # 毛利率预警
    "MarginAlertConfig",
    "MarginAlertRecord",
    "MarginAlertLevelEnum",
    "MarginAlertStatusEnum",
    # 评估模板和工作流
    "AssessmentTemplate",
    "AssessmentItem",
    "AssessmentRisk",
    "AssessmentVersion",
    "AssessmentDimensionEnum",
    "TemplateCategoryEnum",
    "RiskLevelEnum",
    "RiskStatusEnum",
    # 销售漏斗状态机
    "SalesFunnelStage",
    "StageGateConfig",
    "StageGateResult",
    "StageDwellTimeConfig",
    "StageDwellTimeAlert",
    "FunnelTransitionLog",
    "FunnelSnapshot",
    "FunnelEntityTypeEnum",
    "GateTypeEnum",
    "GateResultEnum",
    "AlertSeverityEnum",
    "AlertStatusEnum",
]
