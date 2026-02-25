# -*- coding: utf-8 -*-
"""
数据模型包

导出所有ORM模型供外部使用

注意：此文件包含所有模型的导出。
如需按业务域分组导入，可以使用可选的分组导出模块（app/models/exports/complete/）：
    from app.models.exports.complete.project_related import Project, Task
    from app.models.exports.complete.material_purchase import Material, BomHeader
    # 等等...

但原有的导入方式仍然有效（推荐）：
    from app.models import Project, Material, User
"""

# Import models from complete directory instead of deprecated main
from .exports.complete import *

# 枚举补充导出（向后兼容）
from .enums import ApprovalRecordStatusEnum  # noqa: F401

# AI Knowledge Base & Presale AI System
from .presale_knowledge_case import PresaleKnowledgeCase  # noqa: F401
from .presale_ai_qa import PresaleAIQA  # noqa: F401
from .presale_ai_requirement_analysis import PresaleAIRequirementAnalysis  # noqa: F401
from .presale_ai_solution import (  # noqa: F401
    PresaleAISolution,
    PresaleAISolutionTemplate,
    PresaleAIGenerationLog,
)
from .presale_ai_quotation import (  # noqa: F401
    PresaleAIQuotation,
    QuotationTemplate,
    QuotationApproval,
    QuotationVersion,
)
from .presale_ai_emotion_analysis import PresaleAIEmotionAnalysis  # noqa: F401
from .presale_emotion_trend import PresaleEmotionTrend  # noqa: F401
from .presale_ai import (  # noqa: F401
    PresaleAIUsageStats,
    PresaleAIFeedback,
    PresaleAIConfig,
    PresaleAIWorkflowLog,
    PresaleAIAuditLog,
)
from .presale_mobile import (  # noqa: F401
    PresaleMobileAssistantChat,
    PresaleVisitRecord,
    PresaleMobileQuickEstimate,
    PresaleMobileOfflineData,
)
from .presale_expense import PresaleExpense  # noqa: F401
from .presale_follow_up_reminder import PresaleFollowUpReminder  # noqa: F401
from .sales.presale_ai_cost import (  # noqa: F401
    PresaleAICostEstimation,
    PresaleCostHistory,
    PresaleCostOptimizationRecord,
)
from .sales.presale_ai_win_rate import (  # noqa: F401
    PresaleAIWinRate,
    PresaleWinRateHistory,
)

# Security & Authentication
from .login_attempt import LoginAttempt  # noqa: F401
from .two_factor import User2FASecret, User2FABackupCode  # noqa: F401

# Report System
from .report import (  # noqa: F401
    TimesheetReportTemplate,
    ReportArchive,
    ReportRecipient,
    ReportTypeEnum,
    OutputFormatEnum,
    FrequencyEnum,
    GeneratedByEnum,
    ArchiveStatusEnum,
    RecipientTypeEnum,
    DeliveryMethodEnum,
)

# Project Schedule Prediction System
from .project.schedule_prediction import (  # noqa: F401
    ProjectSchedulePrediction,
    CatchUpSolution,
    ScheduleAlert,
)

# Quality Risk Detection System
from .quality_risk_detection import (  # noqa: F401
    QualityRiskDetection,
    QualityTestRecommendation,
    RiskLevelEnum,
    RiskSourceEnum,
    RiskStatusEnum,
    RiskCategoryEnum,
    TestRecommendationStatusEnum,
    TestPriorityEnum,
)

# Change Request System
from .change_request import (  # noqa: F401
    ChangeRequest,
    ChangeApprovalRecord,
    ChangeNotification,
)

# Change Impact Analysis System
from .change_impact import (  # noqa: F401
    ChangeImpactAnalysis,
    ChangeResponseSuggestion,
)

# Purchase Intelligence System
from .purchase_intelligence import (  # noqa: F401
    PurchaseSuggestion,
    SupplierQuotation,
    SupplierPerformance,
    PurchaseOrderTracking,
)

# Inventory Tracking System
from .inventory_tracking import (  # noqa: F401
    MaterialTransaction,
    MaterialStock,
    MaterialReservation,
    StockCountTask,
    StockCountDetail,
    StockAdjustment,
)

# Smart Shortage Alert System
from .shortage.smart_alert import (  # noqa: F401
    ShortageAlert as ShortageAlertEnhanced,  # Alias for consistency
    ShortageHandlingPlan,
    MaterialDemandForecast,
)

# Material Shortage (from material.py)
from .material import MaterialShortage  # noqa: F401

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "get_engine",
    "get_session",
    "init_db",
    # Tenant
    "Tenant",
    "TenantStatus",
    "TenantPlan",
    # User
    "User",
    "Role",
    "ApiPermission",
    "RoleApiPermission",
    "UserRole",
    "PermissionAudit",
    "UserSession",
    "LoginAttempt",
    "User2FASecret",
    "User2FABackupCode",
    # Project
    "Project",
    "Machine",
    "ProjectStage",
    "ProjectStatus",
    "ProjectMember",
    "ProjectMilestone",
    "ProjectPaymentPlan",
    "ProjectCost",
    "FinancialProjectCost",
    "ProjectDocument",
    "Customer",
    "ProjectStatusLog",
    "ProjectTemplate",
    "ProjectMemberContribution",
    # Earned Value Management (EVM)
    "EarnedValueData",
    "EarnedValueSnapshot",
    # Cost Prediction & Optimization
    "CostPrediction",
    "CostOptimizationSuggestion",
    # Budget
    "ProjectBudget",
    "ProjectBudgetItem",
    "ProjectCostAllocationRule",
    # Material
    "Material",
    "MaterialCategory",
    "Vendor",
    "MaterialSupplier",
    "BomHeader",
    "BomItem",
    "MaterialShortage",
    # Shortage
    "ShortageReport",
    "MaterialArrival",
    "ArrivalFollowUp",
    "MaterialSubstitution",
    "MaterialTransfer",
    "WorkOrderBom",
    "MaterialRequirement",
    "KitCheck",
    "AlertHandleLog",
    "ShortageDailyReport",
    # ShortageAlert 已废弃 - 使用 AlertRecord.target_type='SHORTAGE'
    # Purchase
    "PurchaseOrder",
    "PurchaseOrderItem",
    "GoodsReceipt",
    "GoodsReceiptItem",
    "PurchaseRequest",
    "PurchaseRequestItem",
    # ECN
    "Ecn",
    "EcnEvaluation",
    "EcnApproval",
    "EcnTask",
    "EcnAffectedMaterial",
    "EcnAffectedOrder",
    "EcnLog",
    "EcnType",
    "EcnApprovalMatrix",
    # Acceptance
    "AcceptanceTemplate",
    "TemplateCategory",
    "TemplateCheckItem",
    "AcceptanceOrder",
    "AcceptanceOrderItem",
    "AcceptanceIssue",
    "IssueFollowUp",
    "AcceptanceSignature",
    "AcceptanceReport",
    # Issue
    "Issue",
    "IssueFollowUpRecord",
    "IssueStatisticsSnapshot",
    "IssueTemplate",
    "SolutionTemplate",
    # Outsourcing
    "OutsourcingOrder",
    "OutsourcingOrderItem",
    "OutsourcingDelivery",
    "OutsourcingDeliveryItem",
    "OutsourcingInspection",
    "OutsourcingPayment",
    "OutsourcingEvaluation",
    "OutsourcingProgress",
    # Alert
    "AlertRule",
    "AlertRecord",
    "AlertNotification",
    "ExceptionEvent",
    "ExceptionAction",
    "ExceptionEscalation",
    "AlertStatistics",
    "ProjectHealthSnapshot",
    "AlertRuleTemplate",
    "AlertSubscription",
    # Scheduler Config
    "SchedulerTaskConfig",
    # Production
    "Workshop",
    "Workstation",
    "Worker",
    "WorkerSkill",
    "ProcessDict",
    "Equipment",
    "EquipmentMaintenance",
    "ProductionPlan",
    "WorkOrder",
    "WorkReport",
    "ProductionException",
    "MaterialRequisition",
    "MaterialRequisitionItem",
    "ProductionDailyReport",
    # PMO
    "PmoProjectInitiation",
    "PmoProjectPhase",
    "PmoChangeRequest",
    "PmoProjectRisk",
    "PmoProjectCost",
    "PmoMeeting",
    "PmoResourceAllocation",
    "PmoProjectClosure",
    # Task Center
    "TaskUnified",
    "JobDutyTemplate",
    "TaskOperationLog",
    "TaskComment",
    "TaskReminder",
    # Presale
    "PresaleSupportTicket",
    "PresaleTicketDeliverable",
    "PresaleTicketProgress",
    "PresaleSolution",
    "PresaleSolutionCost",
    "PresaleSolutionTemplate",
    "PresaleWorkload",
    "PresaleCustomerTechProfile",
    "PresaleTenderRecord",
    # Performance
    "PerformancePeriod",
    "PerformanceIndicator",
    "PerformanceResult",
    "PerformanceEvaluation",
    "PerformanceAppeal",
    "ProjectContribution",
    "PerformanceRankingSnapshot",
    "PerformanceAdjustmentHistory",
    # New Performance System
    "MonthlyWorkSummary",
    "PerformanceEvaluationRecord",
    "EvaluationWeightConfig",
    # Timesheet
    "Timesheet",
    "TimesheetBatch",
    "TimesheetSummary",
    "OvertimeApplication",
    "TimesheetApprovalLog",
    "TimesheetRule",
    # Report Center
    "ReportTemplate",
    "ReportDefinition",
    "ReportGeneration",
    "ReportSubscription",
    "DataImportTask",
    "DataExportTask",
    "ImportTemplate",
    # Stage Template
    "StageTemplate",
    "StageDefinition",
    "NodeDefinition",
    "ProjectStageInstance",
    "ProjectNodeInstance",
    "NodeTask",
    # Technical Spec
    "TechnicalSpecRequirement",
    "SpecMatchRecord",
    # Progress
    "WbsTemplate",
    "WbsTemplateTask",
    "Task",
    "TaskDependency",
    "ProgressLog",
    "ScheduleBaseline",
    "BaselineTask",
    "ProgressReport",
    # Notification
    "Notification",
    "NotificationSettings",
    # Sales
    "Lead",
    "LeadFollowUp",
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
    "ContractTemplate",
    "ContractTemplateVersion",
    "Contract",
    "ContractDeliverable",
    "ContractAmendment",
    "Invoice",
    "ReceivableDispute",
    "SalesTarget",
    "QuoteApproval",
    "ContractApproval",
    "InvoiceApproval",
    # Technical Assessment
    "TechnicalAssessment",
    "ScoringRule",
    "FailureCase",
    "LeadRequirementDetail",
    "RequirementFreeze",
    "OpenItem",
    "AIClarification",
    # Approval Workflow
    "ApprovalWorkflow",
    "ApprovalWorkflowStep",
    "ApprovalRecord",
    "ApprovalHistory",
    "ApprovalRecordStatusEnum",
    # Business Support
    "BiddingProject",
    "BiddingDocument",
    "ContractReview",
    "ContractSealRecord",
    "PaymentReminder",
    "DocumentArchive",
    "SalesOrder",
    "SalesOrderItem",
    "DeliveryOrder",
    "AcceptanceTracking",
    "AcceptanceTrackingRecord",
    "Reconciliation",
    "InvoiceRequest",
    "CustomerSupplierRegistration",
    # Service
    "ServiceTicket",
    "ServiceTicketProject",
    "ServiceTicketCcUser",
    "ServiceRecord",
    "CustomerCommunication",
    "CustomerSatisfaction",
    "KnowledgeBase",
    # Pitfall
    "Pitfall",
    "PitfallRecommendation",
    "PitfallLearningProgress",
    # SLA
    "SLAPolicy",
    "SLAMonitor",
    "SLAStatusEnum",
    # Installation Dispatch
    "InstallationDispatchOrder",
    "InstallationDispatchTaskTypeEnum",
    "InstallationDispatchStatusEnum",
    "InstallationDispatchPriorityEnum",
    # RD Project
    "RdProjectCategory",
    "RdProject",
    "RdCostType",
    "RdCost",
    "RdCostAllocationRule",
    "RdReportRecord",
    # Project Review
    "ProjectReview",
    "ProjectLesson",
    "ProjectBestPractice",
    # Technical Review
    "TechnicalReview",
    "ReviewParticipant",
    "ReviewMaterial",
    "ReviewChecklistRecord",
    "ReviewIssue",
    # Bonus
    "BonusRule",
    "BonusCalculation",
    "BonusDistribution",
    "TeamBonusAllocation",
    "BonusAllocationSheet",
    # Project Evaluation
    "ProjectEvaluation",
    "ProjectEvaluationDimension",
    # Hourly Rate
    "HourlyRateConfig",
    # Qualification
    "QualificationLevel",
    "PositionCompetencyModel",
    "EmployeeQualification",
    "QualificationAssessment",
    # Assembly Kit Analysis
    "AssemblyStage",
    "AssemblyTemplate",
    "CategoryStageMapping",
    "BomItemAssemblyAttrs",
    "MaterialReadiness",
    "ShortageDetail",
    "ShortageAlertRule",
    "SchedulingSuggestion",
    # Staff Matching
    "HrTagDict",
    "HrEmployeeTagEvaluation",
    "HrEmployeeProfile",
    "HrProjectPerformance",
    "MesProjectStaffingNeed",
    "HrAIMatchingLog",
    # Project Role Config
    "ProjectRoleType",
    "ProjectRoleConfig",
    "RoleCategoryEnum",
    "ProjectRoleCodeEnum",
    # Management Rhythm
    "ManagementRhythmConfig",
    "StrategicMeeting",
    "MeetingActionItem",
    "RhythmDashboardSnapshot",
    "MeetingReport",
    "MeetingReportConfig",
    "ReportMetricDefinition",
    # Culture Wall
    "CultureWallContent",
    "PersonalGoal",
    "CultureWallReadRecord",
    "CultureWallConfig",
    # Work Log
    "WorkLog",
    "WorkLogConfig",
    "WorkLogMention",
    # Organization
    "Department",
    "Employee",
    "EmployeeHrProfile",
    "HrTransaction",
    "EmployeeContract",
    "ContractReminder",
    "SalaryRecord",
    # Finance - 融资模块已废弃删除
    # Standard Cost
    "StandardCost",
    "StandardCostHistory",
    # Presale Expense
    "PresaleExpense",
    # Pipeline Analysis
    "PipelineBreakRecord",
    "PipelineHealthSnapshot",
    "AccountabilityRecord",
    # Organization V2 - 灵活组织架构
    "OrganizationUnit",
    "Position",
    "JobLevel",
    "EmployeeOrgAssignment",
    "PositionRole",
    "OrganizationUnitType",
    "PositionCategory",
    "JobLevelCategory",
    "AssignmentType",
    # Permission V2 - 灵活权限系统
    "DataScopeRule",
    "RoleDataScope",
    "PermissionGroup",
    "MenuPermission",
    "RoleMenu",
    "ScopeType",
    "MenuType",
    "PermissionType",
    "ResourceType",
    # Unified Approval System - 统一审批系统
    "ApprovalTemplate",
    "ApprovalTemplateVersion",
    "ApprovalFlowDefinition",
    "ApprovalNodeDefinition",
    "ApprovalRoutingRule",
    "ApprovalInstance",
    "ApprovalTask",
    "ApprovalCarbonCopy",
    "ApprovalCountersignResult",
    "ApprovalActionLog",
    "ApprovalComment",
    "ApprovalDelegate",
    "ApprovalDelegateLog",
    # Strategy Management - BEM 战略管理
    "Strategy",
    "CSF",
    "KPI",
    "KPIHistory",
    "KPIDataSource",
    "AnnualKeyWork",
    "AnnualKeyWorkProjectLink",
    "DepartmentObjective",
    "PersonalKPI",
    "StrategyReview",
    "StrategyCalendarEvent",
    "StrategyComparison",
    # AI Knowledge Base
    "PresaleKnowledgeCase",
    "PresaleAIQA",
    # Report System
    "TimesheetReportTemplate",
    "ReportArchive",
    "ReportRecipient",
    "ReportTypeEnum",
    "OutputFormatEnum",
    "FrequencyEnum",
    "GeneratedByEnum",
    "ArchiveStatusEnum",
    "RecipientTypeEnum",
    "DeliveryMethodEnum",
    # Change Impact Analysis System
    "ChangeImpactAnalysis",
    "ChangeResponseSuggestion",
    # Purchase Intelligence System
    "PurchaseSuggestion",
    "SupplierQuotation",
    "SupplierPerformance",
    "PurchaseOrderTracking",
    # Inventory Tracking System
    "MaterialTransaction",
    "MaterialStock",
    "MaterialReservation",
    "StockCountTask",
    "StockCountDetail",
    "StockAdjustment",
    # Smart Shortage Alert System
    "ShortageAlertEnhanced",
    "ShortageHandlingPlan",
    "MaterialDemandForecast",
]
