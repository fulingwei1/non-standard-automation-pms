# -*- coding: utf-8 -*-
"""
完整模型导出 - 其他业务模块
"""
# 预警系统
from ...alert import (
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

# 问题管理
from ...issue import (
    Issue,
    IssueFollowUpRecord,
    IssueStatisticsSnapshot,
    IssueTemplate,
    SolutionTemplate,
)

# 商务支持
from ...business_support import (
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
from ...culture_wall import CultureWallContent, CultureWallReadRecord, PersonalGoal
from ...culture_wall_config import CultureWallConfig

# 财务管理 - 融资模块已废弃删除

# 安装派工
from ...installation_dispatch import (
    InstallationDispatchOrder,
    InstallationDispatchPriorityEnum,
    InstallationDispatchStatusEnum,
    InstallationDispatchTaskTypeEnum,
)

# 管理节奏
from ...management_rhythm import (
    ManagementRhythmConfig,
    MeetingActionItem,
    MeetingReport,
    MeetingReportConfig,
    ReportMetricDefinition,
    RhythmDashboardSnapshot,
    StrategicMeeting,
)

# 通知中心
from ...notification import (
    Notification,
    NotificationSettings,
)

# 陷阱管理
from ...pitfall import (
    Pitfall,
    PitfallLearningProgress,
    PitfallRecommendation,
)

# PMO项目管理
from ...pmo import (
    PmoChangeRequest,
    PmoMeeting,
    PmoProjectClosure,
    PmoProjectCost,
    PmoProjectInitiation,
    PmoProjectPhase,
    PmoProjectRisk,
    PmoResourceAllocation,
)

# 权限系统V2
from ...permission import (
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

# 管道分析
from ...pipeline_analysis import (
    AccountabilityRecord,
    PipelineBreakRecord,
    PipelineHealthSnapshot,
)

# 售前支持
from ...presale import (
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
from ...presale_expense import PresaleExpense

# 报表中心
from ...report_center import (
    DataExportTask,
    DataImportTask,
    ImportTemplate,
    ReportDefinition,
    ReportGeneration,
    ReportSubscription,
    ReportTemplate,
)

# 调度配置
from ...scheduler_config import SchedulerTaskConfig

# 服务管理
from ...service import (
    CustomerCommunication,
    CustomerSatisfaction,
    KnowledgeBase,
    ServiceRecord,
    ServiceTicket,
    ServiceTicketCcUser,
    ServiceTicketProject,
)

# SLA管理
from ...sla import SLAMonitor, SLAPolicy, SLAStatusEnum

# 任务中心
from ...task_center import (
    JobDutyTemplate,
    TaskComment,
    TaskOperationLog,
    TaskReminder,
    TaskUnified,
)

# 技术评审
from ...technical_review import (
    ReviewChecklistRecord,
    ReviewIssue,
    ReviewMaterial,
    ReviewParticipant,
    TechnicalReview,
)

# 技术规格
from ...technical_spec import SpecMatchRecord, TechnicalSpecRequirement

# 工时表
from ...timesheet import (
    OvertimeApplication,
    Timesheet,
    TimesheetApprovalLog,
    TimesheetBatch,
    TimesheetRule,
    TimesheetSummary,
)

# 工作日志
from ...work_log import WorkLog, WorkLogConfig, WorkLogMention

# 研发项目
from ...rd_project import (
    RdCost,
    RdCostAllocationRule,
    RdCostType,
    RdProject,
    RdProjectCategory,
    RdReportRecord,
)

# 奖金管理
from ...bonus import (
    BonusAllocationSheet,
    BonusCalculation,
    BonusDistribution,
    BonusRule,
    TeamBonusAllocation,
)

# 战略管理
from ...strategy import (
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

# 标准成本库
from ...standard_cost import (
    StandardCost,
    StandardCostHistory,
)

__all__ = [
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
    # Issue
    "Issue",
    "IssueFollowUpRecord",
    "IssueStatisticsSnapshot",
    "IssueTemplate",
    "SolutionTemplate",
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
    # Culture Wall
    "CultureWallContent",
    "PersonalGoal",
    "CultureWallReadRecord",
    "CultureWallConfig",
    # Finance - 融资模块已废弃删除
    # Installation Dispatch
    "InstallationDispatchOrder",
    "InstallationDispatchTaskTypeEnum",
    "InstallationDispatchStatusEnum",
    "InstallationDispatchPriorityEnum",
    # Management Rhythm
    "ManagementRhythmConfig",
    "StrategicMeeting",
    "MeetingActionItem",
    "RhythmDashboardSnapshot",
    "MeetingReport",
    "MeetingReportConfig",
    "ReportMetricDefinition",
    # Notification
    "Notification",
    "NotificationSettings",
    # Pitfall
    "Pitfall",
    "PitfallRecommendation",
    "PitfallLearningProgress",
    # PMO
    "PmoProjectInitiation",
    "PmoProjectPhase",
    "PmoChangeRequest",
    "PmoProjectRisk",
    "PmoProjectCost",
    "PmoMeeting",
    "PmoResourceAllocation",
    "PmoProjectClosure",
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
    # Pipeline Analysis
    "PipelineBreakRecord",
    "PipelineHealthSnapshot",
    "AccountabilityRecord",
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
    # Presale Expense
    "PresaleExpense",
    # Report Center
    "ReportTemplate",
    "ReportDefinition",
    "ReportGeneration",
    "ReportSubscription",
    "DataImportTask",
    "DataExportTask",
    "ImportTemplate",
    # Scheduler Config
    "SchedulerTaskConfig",
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
    # Task Center
    "TaskUnified",
    "JobDutyTemplate",
    "TaskOperationLog",
    "TaskComment",
    "TaskReminder",
    # Technical Review
    "TechnicalReview",
    "ReviewParticipant",
    "ReviewMaterial",
    "ReviewChecklistRecord",
    "ReviewIssue",
    # Technical Spec
    "TechnicalSpecRequirement",
    "SpecMatchRecord",
    # Timesheet
    "Timesheet",
    "TimesheetBatch",
    "TimesheetSummary",
    "OvertimeApplication",
    "TimesheetApprovalLog",
    "TimesheetRule",
    # Work Log
    "WorkLog",
    "WorkLogConfig",
    "WorkLogMention",
    # RD Project
    "RdProjectCategory",
    "RdProject",
    "RdCostType",
    "RdCost",
    "RdCostAllocationRule",
    "RdReportRecord",
    # Bonus
    "BonusRule",
    "BonusCalculation",
    "BonusDistribution",
    "TeamBonusAllocation",
    "BonusAllocationSheet",
    # Strategy
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
    # Standard Cost
    "StandardCost",
    "StandardCostHistory",
]
