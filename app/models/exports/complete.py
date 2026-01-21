# -*- coding: utf-8 -*-
"""
完整模型导出模块
包含所有未在其他分组文件中的模型
"""

# 基础模型
from ..base import Base, TimestampMixin, get_engine, get_session, init_db

# 枚举
from ..enums import *

# 验收管理
from ..acceptance import (
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

# 预警系统
from ..alert import (
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

# 装配套件分析
from ..assembly_kit import (
    AssemblyStage,
    AssemblyTemplate,
    BomItemAssemblyAttrs,
    CategoryStageMapping,
    MaterialReadiness,
    SchedulingSuggestion,
    ShortageAlertRule,
    ShortageDetail,
)

# 预算管理
from ..budget import ProjectBudget, ProjectBudgetItem, ProjectCostAllocationRule

# 商务支持
from ..business_support import (
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

# 文化墙
from ..culture_wall import CultureWallContent, CultureWallReadRecord, PersonalGoal
from ..culture_wall_config import CultureWallConfig

# ECN工程变更
from ..ecn import (
    Ecn,
    EcnAffectedMaterial,
    EcnAffectedOrder,
    EcnApproval,
    EcnApprovalMatrix,
    EcnEvaluation,
    EcnLog,
    EcnResponsibility,
    EcnSolutionTemplate,
    EcnTask,
    EcnType,
)

# 财务管理
from ..finance import (
    EquityStructure,
    FundingRecord,
    FundingRound,
    FundingUsage,
    Investor,
)

# 时薪配置
from ..hourly_rate import HourlyRateConfig

# 安装派工
from ..installation_dispatch import (
    InstallationDispatchOrder,
    InstallationDispatchPriorityEnum,
    InstallationDispatchStatusEnum,
    InstallationDispatchTaskTypeEnum,
)

# 问题管理
from ..issue import (
    Issue,
    IssueFollowUpRecord,
    IssueStatisticsSnapshot,
    IssueTemplate,
    SolutionTemplate,
)

# 管理节奏
from ..management_rhythm import (
    ManagementRhythmConfig,
    MeetingActionItem,
    MeetingReport,
    MeetingReportConfig,
    ReportMetricDefinition,
    RhythmDashboardSnapshot,
    StrategicMeeting,
)

# 物料管理
from ..material import (
    BomHeader,
    BomItem,
    Material,
    MaterialCategory,
    MaterialSupplier,
    Supplier,
)

# 外协管理
from ..outsourcing import (
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

# 采购管理
from ..purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)

# 项目相关
from ..project import (
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

# 项目评估
from ..project_evaluation import ProjectEvaluation, ProjectEvaluationDimension

# 项目复盘
from ..project_review import ProjectBestPractice, ProjectLesson, ProjectReview

# 项目角色配置
from ..project_role import (
    ProjectRoleCodeEnum,
    ProjectRoleConfig,
    ProjectRoleType,
    RoleCategoryEnum,
)

# 生产管理
from ..production import (
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

# 进度管理
from ..progress import (
    BaselineTask,
    ProgressLog,
    ProgressReport,
    ScheduleBaseline,
    Task,
    TaskDependency,
    WbsTemplate,
    WbsTemplateTask,
)

# 研发项目
from ..rd_project import (
    RdCost,
    RdCostAllocationRule,
    RdCostType,
    RdProject,
    RdProjectCategory,
    RdReportRecord,
)

# 阶段实例
from ..stage_instance import (
    NodeTask,
    ProjectNodeInstance,
    ProjectStageInstance,
)

# 阶段模板
from ..stage_template import (
    NodeDefinition,
    StageDefinition,
    StageTemplate,
)

# 通知中心
from ..notification import (
    Notification,
    NotificationSettings,
)

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
    MaterialCostUpdateReminder,
)

# 调度配置
from ..scheduler_config import SchedulerTaskConfig

# 服务管理
from ..service import (
    CustomerCommunication,
    CustomerSatisfaction,
    KnowledgeBase,
    ServiceRecord,
    ServiceTicket,
    ServiceTicketCcUser,
    ServiceTicketProject,
)

# 陷阱管理
from ..pitfall import (
    Pitfall,
    PitfallLearningProgress,
    PitfallRecommendation,
)

# 短缺管理
from ..shortage import (
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

# SLA管理
from ..sla import SLAMonitor, SLAPolicy, SLAStatusEnum

# 人员匹配
from ..staff_matching import (
    HrAIMatchingLog,
    HrEmployeeProfile,
    HrEmployeeTagEvaluation,
    HrProjectPerformance,
    HrTagDict,
    MesProjectStaffingNeed,
)

# 任务中心
from ..task_center import (
    JobDutyTemplate,
    TaskComment,
    TaskOperationLog,
    TaskReminder,
    TaskUnified,
)

# 技术评审
from ..technical_review import (
    ReviewChecklistRecord,
    ReviewIssue,
    ReviewMaterial,
    ReviewParticipant,
    TechnicalReview,
)

# 技术规格
from ..technical_spec import SpecMatchRecord, TechnicalSpecRequirement

# 工时表
from ..timesheet import (
    OvertimeApplication,
    Timesheet,
    TimesheetApprovalLog,
    TimesheetBatch,
    TimesheetRule,
    TimesheetSummary,
)

# 用户权限
from ..user import Permission, PermissionAudit, Role, RolePermission, User, UserRole

# 工作日志
from ..work_log import WorkLog, WorkLogConfig, WorkLogMention

# 统一审批系统
from ..approval import (
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

# 战略管理
from ..strategy import (
    AnnualKeyWork,
    AnnualKeyWorkProjectLink,
    CSF,
    DepartmentObjective,
    KPI,
    KPIDataSource,
    KPIHistory,
    PersonalKPI,
    Strategy,
    StrategyCalendarEvent,
    StrategyComparison,
    StrategyReview,
)

# PMO项目管理
from ..pmo import (
    PmoChangeRequest,
    PmoMeeting,
    PmoProjectClosure,
    PmoProjectCost,
    PmoProjectInitiation,
    PmoProjectPhase,
    PmoProjectRisk,
    PmoResourceAllocation,
)

# 售前支持
from ..presale import (
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

# 售前费用
from ..presale_expense import PresaleExpense

# 绩效管理
from ..performance import (
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

# 报表中心
from ..report_center import (
    DataExportTask,
    DataImportTask,
    ImportTemplate,
    ReportDefinition,
    ReportGeneration,
    ReportSubscription,
    ReportTemplate,
)

# 管道分析
from ..pipeline_analysis import (
    AccountabilityRecord,
    PipelineBreakRecord,
    PipelineHealthSnapshot,
)

# 组织架构
from ..organization import (
    ContractReminder,
    Department,
    Employee,
    EmployeeContract,
    EmployeeHrProfile,
    HrTransaction,
    SalaryRecord,
)

# 组织架构V2
from ..organization_v2 import (
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

# 权限系统V2
from ..permission_v2 import (
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

# 资格认证
from ..qualification import (
    EmployeeQualification,
    PositionCompetencyModel,
    QualificationAssessment,
    QualificationLevel,
)

# 奖金管理
from ..bonus import (
    BonusAllocationSheet,
    BonusCalculation,
    BonusDistribution,
    BonusRule,
    TeamBonusAllocation,
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
    "ProjectTemplateVersion",
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
    "EcnResponsibility",
    "EcnSolutionTemplate",
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
    # Organization V2
    "OrganizationUnit",
    "Position",
    "JobLevel",
    "EmployeeOrgAssignment",
    "PositionRole",
    "OrganizationUnitType",
    "PositionCategory",
    "JobLevelCategory",
    "AssignmentType",
    # Permission V2
    "DataScopeRule",
    "RoleDataScope",
    "PermissionGroup",
    "MenuPermission",
    "RoleMenu",
    "ScopeType",
    "MenuType",
    "PermissionType",
    "ResourceType",
    # Unified Approval System
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
    # Strategy Management
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
]
