# -*- coding: utf-8 -*-
"""
数据模型包

导出所有ORM模型供外部使用

注意：此文件包含所有模型的导出（762行）。
如需按业务域分组导入，可以使用可选的分组导出模块（app/models/exports/）：
    from app.models.exports.project_models import Project, Task
    from app.models.exports.material_models import Material, BomHeader
    # 等等...

但原有的导入方式仍然有效（推荐）：
    from app.models import Project, Material, User
"""

from .acceptance import (
    AcceptanceIssue,
    AcceptanceOrder,
    AcceptanceOrderItem,
    AcceptanceReport,
    AcceptanceSignature,
    AcceptanceTemplate,
    IssueFollowUp,
    TemplateCategory,
    TemplateCheckItem,
)
from .alert import (
    AlertNotification,
    AlertRecord,
    AlertRule,
    AlertRuleTemplate,
    AlertStatistics,
    AlertSubscription,
    ExceptionAction,
    ExceptionEscalation,
    ExceptionEvent,
    ProjectHealthSnapshot,
)
from .assembly_kit import (
    AssemblyStage,
    AssemblyTemplate,
    BomItemAssemblyAttrs,
    CategoryStageMapping,
    MaterialReadiness,
    SchedulingSuggestion,
    ShortageAlertRule,
    ShortageDetail,
)
from .base import Base, TimestampMixin, get_engine, get_session, init_db
from .bonus import (
    BonusAllocationSheet,
    BonusCalculation,
    BonusDistribution,
    BonusRule,
    TeamBonusAllocation,
)
from .budget import ProjectBudget, ProjectBudgetItem, ProjectCostAllocationRule
from .business_support import (
    AcceptanceTracking,
    AcceptanceTrackingRecord,
    BiddingDocument,
    BiddingProject,
    ContractReview,
    ContractSealRecord,
    CustomerSupplierRegistration,
    DeliveryOrder,
    DocumentArchive,
    InvoiceRequest,
    PaymentReminder,
    Reconciliation,
    SalesOrder,
    SalesOrderItem,
)
from .culture_wall import CultureWallContent, CultureWallReadRecord, PersonalGoal
from .culture_wall_config import CultureWallConfig
from .ecn import (
    Ecn,
    EcnAffectedMaterial,
    EcnAffectedOrder,
    EcnApproval,
    EcnApprovalMatrix,
    EcnBomImpact,
    EcnEvaluation,
    EcnLog,
    EcnResponsibility,
    EcnSolutionTemplate,
    EcnTask,
    EcnType,
)
from .enums import *
from .finance import (
    EquityStructure,
    FundingRecord,
    FundingRound,
    FundingUsage,
    Investor,
)
from .hourly_rate import HourlyRateConfig
from .installation_dispatch import (
    InstallationDispatchOrder,
    InstallationDispatchPriorityEnum,
    InstallationDispatchStatusEnum,
    InstallationDispatchTaskTypeEnum,
)
from .issue import (
    Issue,
    IssueFollowUpRecord,
    IssueStatisticsSnapshot,
    IssueTemplate,
    SolutionTemplate,
)
from .management_rhythm import (
    ManagementRhythmConfig,
    MeetingActionItem,
    MeetingReport,
    MeetingReportConfig,
    ReportMetricDefinition,
    RhythmDashboardSnapshot,
    StrategicMeeting,
)
from .material import (
    BomHeader,
    BomItem,
    Material,
    MaterialCategory,
    MaterialShortage,
    MaterialSupplier,
    Supplier,
)
from .notification import Notification, NotificationSettings
from .organization import (
    ContractReminder,
    Department,
    Employee,
    EmployeeContract,
    EmployeeHrProfile,
    HrTransaction,
    SalaryRecord,
)

# Organization V2 - 灵活组织架构
from .organization_v2 import (
    AssignmentType,
    EmployeeOrgAssignment,
    JobLevel,
    JobLevelCategory,
    OrganizationUnit,
    OrganizationUnitType,
    Position,
    PositionCategory,
    PositionRole,
)
from .outsourcing import (
    OutsourcingDelivery,
    OutsourcingDeliveryItem,
    OutsourcingEvaluation,
    OutsourcingInspection,
    OutsourcingOrder,
    OutsourcingOrderItem,
    OutsourcingPayment,
    OutsourcingProgress,
    OutsourcingVendor,
)
from .performance import (  # New Performance System
    EvaluationWeightConfig,
    MonthlyWorkSummary,
    PerformanceAdjustmentHistory,
    PerformanceAppeal,
    PerformanceEvaluation,
    PerformanceEvaluationRecord,
    PerformanceIndicator,
    PerformancePeriod,
    PerformanceRankingSnapshot,
    PerformanceResult,
    ProjectContribution,
)

# Permission V2 - 灵活权限系统
from .permission_v2 import (
    DataScopeRule,
    MenuPermission,
    MenuType,
    PermissionGroup,
    PermissionType,
    ResourceType,
    RoleDataScope,
    RoleMenu,
    ScopeType,
)
from .pipeline_analysis import (
    AccountabilityRecord,
    PipelineBreakRecord,
    PipelineHealthSnapshot,
)
from .pmo import (
    PmoChangeRequest,
    PmoMeeting,
    PmoProjectClosure,
    PmoProjectCost,
    PmoProjectInitiation,
    PmoProjectPhase,
    PmoProjectRisk,
    PmoResourceAllocation,
)
from .presale import (
    PresaleCustomerTechProfile,
    PresaleSolution,
    PresaleSolutionCost,
    PresaleSolutionTemplate,
    PresaleSupportTicket,
    PresaleTenderRecord,
    PresaleTicketDeliverable,
    PresaleTicketProgress,
    PresaleWorkload,
)
from .presale_expense import PresaleExpense
from .production import (
    Equipment,
    EquipmentMaintenance,
    MaterialRequisition,
    MaterialRequisitionItem,
    ProcessDict,
    ProductionDailyReport,
    ProductionException,
    ProductionPlan,
    Worker,
    WorkerSkill,
    WorkOrder,
    WorkReport,
    Workshop,
    Workstation,
)
from .progress import (
    BaselineTask,
    ProgressLog,
    ProgressReport,
    ScheduleBaseline,
    Task,
    TaskDependency,
    WbsTemplate,
    WbsTemplateTask,
)
from .project import (
    Customer,
    FinancialProjectCost,
    Machine,
    Project,
    ProjectCost,
    ProjectDocument,
    ProjectMember,
    ProjectMemberContribution,
    ProjectMilestone,
    ProjectPaymentPlan,
    ProjectStage,
    ProjectStatus,
    ProjectStatusLog,
    ProjectTemplate,
    ProjectTemplateVersion,
)
from .project_evaluation import ProjectEvaluation, ProjectEvaluationDimension
from .project_review import ProjectBestPractice, ProjectLesson, ProjectReview
from .project_role import (
    ProjectRoleCodeEnum,
    ProjectRoleConfig,
    ProjectRoleType,
    RoleCategoryEnum,
)
from .purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)
from .qualification import (
    EmployeeQualification,
    PositionCompetencyModel,
    QualificationAssessment,
    QualificationLevel,
)
from .rd_project import (
    RdCost,
    RdCostAllocationRule,
    RdCostType,
    RdProject,
    RdProjectCategory,
    RdReportRecord,
)
from .report_center import (
    DataExportTask,
    DataImportTask,
    ImportTemplate,
    ReportDefinition,
    ReportGeneration,
    ReportSubscription,
    ReportTemplate,
)
from .sales import (  # Technical Assessment; Approval Workflow
    AIClarification,
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    Contract,
    ContractAmendment,
    ContractApproval,
    ContractDeliverable,
    ContractTemplate,
    ContractTemplateVersion,
    CpqRuleSet,
    FailureCase,
    Invoice,
    InvoiceApproval,
    Lead,
    LeadFollowUp,
    LeadRequirementDetail,
    OpenItem,
    Opportunity,
    OpportunityRequirement,
    PurchaseMaterialCost,
    Quote,
    QuoteApproval,
    QuoteCostApproval,
    QuoteCostHistory,
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
)
from .scheduler_config import SchedulerTaskConfig
from .service import (
    CustomerCommunication,
    CustomerSatisfaction,
    KnowledgeBase,
    ServiceRecord,
    ServiceTicket,
    ServiceTicketCcUser,
    ServiceTicketProject,
)
from .shortage import (
    AlertHandleLog,
    ArrivalFollowUp,
    KitCheck,
    MaterialArrival,
    MaterialRequirement,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageAlert,
    ShortageDailyReport,
    ShortageReport,
    WorkOrderBom,
)
from .sla import SLAMonitor, SLAPolicy, SLAStatusEnum
from .staff_matching import (
    HrAIMatchingLog,
    HrEmployeeProfile,
    HrEmployeeTagEvaluation,
    HrProjectPerformance,
    HrTagDict,
    MesProjectStaffingNeed,
)
from .task_center import (
    JobDutyTemplate,
    TaskComment,
    TaskOperationLog,
    TaskReminder,
    TaskUnified,
)
from .technical_review import (
    ReviewChecklistRecord,
    ReviewIssue,
    ReviewMaterial,
    ReviewParticipant,
    TechnicalReview,
)
from .technical_spec import SpecMatchRecord, TechnicalSpecRequirement
from .timesheet import (
    OvertimeApplication,
    Timesheet,
    TimesheetApprovalLog,
    TimesheetBatch,
    TimesheetRule,
    TimesheetSummary,
)
from .user import Permission, PermissionAudit, Role, RolePermission, User, UserRole
from .work_log import WorkLog, WorkLogConfig, WorkLogMention

# Unified Approval System - 统一审批系统
from .approval import (
    ApprovalActionLog,
    ApprovalCarbonCopy,
    ApprovalComment,
    ApprovalCountersignResult,
    ApprovalDelegate,
    ApprovalDelegateLog,
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalRoutingRule,
    ApprovalTask,
    ApprovalTemplate,
    ApprovalTemplateVersion,
)

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "get_engine",
    "get_session",
    "init_db",
    # User
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "PermissionAudit",
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
    # Budget
    "ProjectBudget",
    "ProjectBudgetItem",
    "ProjectCostAllocationRule",
    # Material
    "Material",
    "MaterialCategory",
    "Supplier",
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
    "ShortageAlert",
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
    "OutsourcingVendor",
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
    # Finance
    "FundingRound",
    "Investor",
    "FundingRecord",
    "EquityStructure",
    "FundingUsage",
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
]
