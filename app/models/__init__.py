# -*- coding: utf-8 -*-
"""
数据模型包

导出所有ORM模型供外部使用
"""

from .base import Base, TimestampMixin, get_engine, get_session, init_db
from .enums import *
from .user import User, Role, Permission, RolePermission, UserRole, PermissionAudit
from .project import (
    Project, Machine, ProjectStage, ProjectStatus,
    ProjectMember, ProjectMilestone, ProjectPaymentPlan, ProjectCost, FinancialProjectCost, ProjectDocument, Customer,
    ProjectStatusLog, ProjectTemplate, ProjectTemplateVersion
)
from .budget import (
    ProjectBudget, ProjectBudgetItem, ProjectCostAllocationRule
)
from .material import (
    Material, MaterialCategory, Supplier, MaterialSupplier,
    BomHeader, BomItem, MaterialShortage
)
from .shortage import (
    ShortageReport, MaterialArrival, ArrivalFollowUp,
    MaterialSubstitution, MaterialTransfer,
    WorkOrderBom, MaterialRequirement, KitCheck,
    AlertHandleLog, ShortageDailyReport, ShortageAlert
)
from .purchase import (
    PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem,
    PurchaseRequest, PurchaseRequestItem
)
from .ecn import (
    Ecn, EcnEvaluation, EcnApproval, EcnTask,
    EcnAffectedMaterial, EcnAffectedOrder, EcnLog,
    EcnType, EcnApprovalMatrix, EcnBomImpact, EcnResponsibility,
    EcnSolutionTemplate
)
from .acceptance import (
    AcceptanceTemplate, TemplateCategory, TemplateCheckItem,
    AcceptanceOrder, AcceptanceOrderItem, AcceptanceIssue,
    IssueFollowUp, AcceptanceSignature, AcceptanceReport
)
from .issue import Issue, IssueFollowUpRecord, IssueStatisticsSnapshot, IssueTemplate
from .outsourcing import (
    OutsourcingVendor, OutsourcingOrder, OutsourcingOrderItem,
    OutsourcingDelivery, OutsourcingDeliveryItem, OutsourcingInspection,
    OutsourcingPayment, OutsourcingEvaluation, OutsourcingProgress
)
from .alert import (
    AlertRule, AlertRecord, AlertNotification,
    ExceptionEvent, ExceptionAction, ExceptionEscalation,
    AlertStatistics, ProjectHealthSnapshot, AlertRuleTemplate,
    AlertSubscription
)
from .production import (
    Workshop, Workstation, Worker, WorkerSkill, ProcessDict,
    Equipment, EquipmentMaintenance, ProductionPlan,
    WorkOrder, WorkReport, ProductionException,
    MaterialRequisition, MaterialRequisitionItem, ProductionDailyReport
)
from .pmo import (
    PmoProjectInitiation, PmoProjectPhase, PmoChangeRequest,
    PmoProjectRisk, PmoProjectCost, PmoMeeting,
    PmoResourceAllocation, PmoProjectClosure
)
from .task_center import (
    TaskUnified, JobDutyTemplate, TaskOperationLog,
    TaskComment, TaskReminder
)
from .presale import (
    PresaleSupportTicket, PresaleTicketDeliverable, PresaleTicketProgress,
    PresaleSolution, PresaleSolutionCost, PresaleSolutionTemplate,
    PresaleWorkload, PresaleCustomerTechProfile, PresaleTenderRecord
)
from .performance import (
    PerformancePeriod, PerformanceIndicator, PerformanceResult,
    PerformanceEvaluation, PerformanceAppeal, ProjectContribution,
    PerformanceRankingSnapshot,
    # New Performance System
    MonthlyWorkSummary, PerformanceEvaluationRecord, EvaluationWeightConfig
)
from .timesheet import (
    Timesheet, TimesheetBatch, TimesheetSummary,
    OvertimeApplication, TimesheetApprovalLog, TimesheetRule
)
from .report_center import (
    ReportTemplate, ReportDefinition, ReportGeneration,
    ReportSubscription, DataImportTask, DataExportTask, ImportTemplate
)
from .technical_spec import (
    TechnicalSpecRequirement, SpecMatchRecord
)
from .progress import (
    WbsTemplate, WbsTemplateTask, Task, TaskDependency,
    ProgressLog, ScheduleBaseline, BaselineTask, ProgressReport
)
from .notification import (
    Notification, NotificationSettings
)
from .sales import (
    Lead, LeadFollowUp, Opportunity, OpportunityRequirement,
    Quote, QuoteVersion, QuoteItem,
    QuoteCostTemplate, QuoteCostApproval, QuoteCostHistory,
    PurchaseMaterialCost,
    CpqRuleSet, QuoteTemplate, QuoteTemplateVersion,
    ContractTemplate, ContractTemplateVersion,
    Contract, ContractDeliverable, ContractAmendment,
    Invoice, ReceivableDispute,
    QuoteApproval, ContractApproval, InvoiceApproval,
    # Technical Assessment
    TechnicalAssessment, ScoringRule, FailureCase,
    LeadRequirementDetail, RequirementFreeze, OpenItem, AIClarification,
    # Approval Workflow
    ApprovalWorkflow, ApprovalWorkflowStep, ApprovalRecord, ApprovalHistory
)
from .business_support import (
    BiddingProject, BiddingDocument,
    ContractReview, ContractSealRecord,
    PaymentReminder, DocumentArchive,
    SalesOrder, SalesOrderItem, DeliveryOrder,
    AcceptanceTracking, AcceptanceTrackingRecord,
    Reconciliation, InvoiceRequest, CustomerSupplierRegistration
)
from .service import (
    ServiceTicket, ServiceRecord, CustomerCommunication,
    CustomerSatisfaction, KnowledgeBase
)
from .installation_dispatch import (
    InstallationDispatchOrder,
    InstallationDispatchTaskTypeEnum,
    InstallationDispatchStatusEnum,
    InstallationDispatchPriorityEnum
)
from .rd_project import (
    RdProjectCategory, RdProject, RdCostType, RdCost,
    RdCostAllocationRule, RdReportRecord
)
from .project_review import (
    ProjectReview, ProjectLesson, ProjectBestPractice
)
from .technical_review import (
    TechnicalReview, ReviewParticipant, ReviewMaterial,
    ReviewChecklistRecord, ReviewIssue
)
from .bonus import (
    BonusRule, BonusCalculation, BonusDistribution, TeamBonusAllocation, BonusAllocationSheet
)
from .project_evaluation import (
    ProjectEvaluation, ProjectEvaluationDimension
)
from .hourly_rate import (
    HourlyRateConfig
)
from .qualification import (
    QualificationLevel, PositionCompetencyModel,
    EmployeeQualification, QualificationAssessment
)
from .assembly_kit import (
    AssemblyStage, AssemblyTemplate, CategoryStageMapping,
    BomItemAssemblyAttrs, MaterialReadiness, ShortageDetail,
    ShortageAlertRule, SchedulingSuggestion
)
from .staff_matching import (
    HrTagDict, HrEmployeeTagEvaluation, HrEmployeeProfile,
    HrProjectPerformance, MesProjectStaffingNeed, HrAIMatchingLog
)
from .project_role import (
    ProjectRoleType, ProjectRoleConfig,
    RoleCategoryEnum, ProjectRoleCodeEnum
)

__all__ = [
    # Base
    'Base', 'TimestampMixin', 'get_engine', 'get_session', 'init_db',
    # User
    'User', 'Role', 'Permission', 'RolePermission', 'UserRole', 'PermissionAudit',
    # Project
    'Project', 'Machine', 'ProjectStage', 'ProjectStatus',
    'ProjectMember', 'ProjectMilestone', 'ProjectPaymentPlan', 'ProjectCost', 'FinancialProjectCost', 'ProjectDocument', 'Customer',
    'ProjectStatusLog', 'ProjectTemplate',
    # Budget
    'ProjectBudget', 'ProjectBudgetItem', 'ProjectCostAllocationRule',
    # Material
    'Material', 'MaterialCategory', 'Supplier', 'MaterialSupplier',
    'BomHeader', 'BomItem', 'MaterialShortage',
    # Shortage
    'ShortageReport', 'MaterialArrival', 'ArrivalFollowUp',
    'MaterialSubstitution', 'MaterialTransfer',
    'WorkOrderBom', 'MaterialRequirement', 'KitCheck',
    'AlertHandleLog', 'ShortageDailyReport', 'ShortageAlert',
    # Purchase
    'PurchaseOrder', 'PurchaseOrderItem', 'GoodsReceipt', 'GoodsReceiptItem',
    'PurchaseRequest', 'PurchaseRequestItem',
    # ECN
    'Ecn', 'EcnEvaluation', 'EcnApproval', 'EcnTask',
    'EcnAffectedMaterial', 'EcnAffectedOrder', 'EcnLog',
    'EcnType', 'EcnApprovalMatrix',
    # Acceptance
    'AcceptanceTemplate', 'TemplateCategory', 'TemplateCheckItem',
    'AcceptanceOrder', 'AcceptanceOrderItem', 'AcceptanceIssue',
    'IssueFollowUp', 'AcceptanceSignature', 'AcceptanceReport',
    # Issue
    'Issue', 'IssueFollowUpRecord', 'IssueStatisticsSnapshot', 'IssueTemplate',
    # Outsourcing
    'OutsourcingVendor', 'OutsourcingOrder', 'OutsourcingOrderItem',
    'OutsourcingDelivery', 'OutsourcingDeliveryItem', 'OutsourcingInspection',
    'OutsourcingPayment', 'OutsourcingEvaluation', 'OutsourcingProgress',
    # Alert
    'AlertRule', 'AlertRecord', 'AlertNotification',
    'ExceptionEvent', 'ExceptionAction', 'ExceptionEscalation',
    'AlertStatistics', 'ProjectHealthSnapshot', 'AlertRuleTemplate',
    'AlertSubscription',
    # Production
    'Workshop', 'Workstation', 'Worker', 'WorkerSkill', 'ProcessDict',
    'Equipment', 'EquipmentMaintenance', 'ProductionPlan',
    'WorkOrder', 'WorkReport', 'ProductionException',
    'MaterialRequisition', 'MaterialRequisitionItem', 'ProductionDailyReport',
    # PMO
    'PmoProjectInitiation', 'PmoProjectPhase', 'PmoChangeRequest',
    'PmoProjectRisk', 'PmoProjectCost', 'PmoMeeting',
    'PmoResourceAllocation', 'PmoProjectClosure',
    # Task Center
    'TaskUnified', 'JobDutyTemplate', 'TaskOperationLog',
    'TaskComment', 'TaskReminder',
    # Presale
    'PresaleSupportTicket', 'PresaleTicketDeliverable', 'PresaleTicketProgress',
    'PresaleSolution', 'PresaleSolutionCost', 'PresaleSolutionTemplate',
    'PresaleWorkload', 'PresaleCustomerTechProfile', 'PresaleTenderRecord',
    # Performance
    'PerformancePeriod', 'PerformanceIndicator', 'PerformanceResult',
    'PerformanceEvaluation', 'PerformanceAppeal', 'ProjectContribution',
    'PerformanceRankingSnapshot',
    # New Performance System
    'MonthlyWorkSummary', 'PerformanceEvaluationRecord', 'EvaluationWeightConfig',
    # Timesheet
    'Timesheet', 'TimesheetBatch', 'TimesheetSummary',
    'OvertimeApplication', 'TimesheetApprovalLog', 'TimesheetRule',
    # Report Center
    'ReportTemplate', 'ReportDefinition', 'ReportGeneration',
    'ReportSubscription', 'DataImportTask', 'DataExportTask', 'ImportTemplate',
    # Technical Spec
    'TechnicalSpecRequirement', 'SpecMatchRecord',
    # Progress
    'WbsTemplate', 'WbsTemplateTask', 'Task', 'TaskDependency',
    'ProgressLog', 'ScheduleBaseline', 'BaselineTask', 'ProgressReport',
    # Notification
    'Notification', 'NotificationSettings',
    # Sales
    'Lead', 'LeadFollowUp', 'Opportunity', 'OpportunityRequirement',
    'Quote', 'QuoteVersion', 'QuoteItem',
    'QuoteCostTemplate', 'QuoteCostApproval', 'QuoteCostHistory',
    'PurchaseMaterialCost', 'MaterialCostUpdateReminder',
    'CpqRuleSet', 'QuoteTemplate', 'QuoteTemplateVersion',
    'ContractTemplate', 'ContractTemplateVersion',
    'Contract', 'ContractDeliverable', 'ContractAmendment',
    'Invoice', 'ReceivableDispute',
    'QuoteApproval', 'ContractApproval', 'InvoiceApproval',
    # Technical Assessment
    'TechnicalAssessment', 'ScoringRule', 'FailureCase',
    'LeadRequirementDetail', 'RequirementFreeze', 'OpenItem', 'AIClarification',
    # Approval Workflow
    'ApprovalWorkflow', 'ApprovalWorkflowStep', 'ApprovalRecord', 'ApprovalHistory',
    # Business Support
    'BiddingProject', 'BiddingDocument',
    'ContractReview', 'ContractSealRecord',
    'PaymentReminder', 'DocumentArchive',
    'SalesOrder', 'SalesOrderItem', 'DeliveryOrder',
    'AcceptanceTracking', 'AcceptanceTrackingRecord',
    'Reconciliation', 'InvoiceRequest', 'CustomerSupplierRegistration',
    # Service
    'ServiceTicket', 'ServiceRecord', 'CustomerCommunication',
    'CustomerSatisfaction', 'KnowledgeBase',
    # Installation Dispatch
    'InstallationDispatchOrder',
    'InstallationDispatchTaskTypeEnum',
    'InstallationDispatchStatusEnum',
    'InstallationDispatchPriorityEnum',
    # RD Project
    'RdProjectCategory', 'RdProject', 'RdCostType', 'RdCost',
    'RdCostAllocationRule', 'RdReportRecord',
    # Project Review
    'ProjectReview', 'ProjectLesson', 'ProjectBestPractice',
    # Technical Review
    'TechnicalReview', 'ReviewParticipant', 'ReviewMaterial',
    'ReviewChecklistRecord', 'ReviewIssue',
    # Bonus
    'BonusRule', 'BonusCalculation', 'BonusDistribution', 'TeamBonusAllocation', 'BonusAllocationSheet',
    # Project Evaluation
    'ProjectEvaluation', 'ProjectEvaluationDimension',
    # Hourly Rate
    'HourlyRateConfig',
    # Qualification
    'QualificationLevel', 'PositionCompetencyModel',
    'EmployeeQualification', 'QualificationAssessment',
    # Assembly Kit Analysis
    'AssemblyStage', 'AssemblyTemplate', 'CategoryStageMapping',
    'BomItemAssemblyAttrs', 'MaterialReadiness', 'ShortageDetail',
    'ShortageAlertRule', 'SchedulingSuggestion',
    # Staff Matching
    'HrTagDict', 'HrEmployeeTagEvaluation', 'HrEmployeeProfile',
    'HrProjectPerformance', 'MesProjectStaffingNeed', 'HrAIMatchingLog',
    # Project Role Config
    'ProjectRoleType', 'ProjectRoleConfig',
    'RoleCategoryEnum', 'ProjectRoleCodeEnum',
]
