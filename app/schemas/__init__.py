# -*- coding: utf-8 -*-
"""
Pydantic Schema 模块
"""

from .common import (
    ResponseModel, PaginatedResponse, PageParams,
    IdResponse, MessageResponse, StatusUpdate
)
from .auth import Token, TokenData, LoginRequest, UserCreate, UserUpdate, UserResponse, UserRoleAssign
from .project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    MachineCreate, MachineUpdate, MachineResponse,
    MilestoneCreate, MilestoneUpdate, MilestoneResponse
)
from .material import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    SupplierCreate, SupplierUpdate, SupplierResponse,
    BomCreate, BomItemCreate, BomResponse
)
from .purchase import (
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse,
    PurchaseOrderItemCreate, GoodsReceiptCreate
)
from .ecn import (
    EcnCreate, EcnUpdate, EcnResponse,
    EcnEvaluationCreate, EcnApprovalCreate, EcnTaskCreate
)
from .acceptance import (
    AcceptanceOrderCreate, AcceptanceOrderUpdate, AcceptanceOrderResponse,
    CheckItemResultUpdate, AcceptanceIssueCreate
)
from .outsourcing import (
    VendorCreate, VendorUpdate, VendorResponse,
    OutsourcingOrderCreate, OutsourcingOrderUpdate, OutsourcingOrderResponse
)
from .alert import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertRecordResponse, ExceptionEventCreate, ExceptionEventResponse
)
from .technical_spec import (
    TechnicalSpecRequirementCreate, TechnicalSpecRequirementUpdate, TechnicalSpecRequirementResponse,
    TechnicalSpecRequirementListResponse, SpecMatchRecordResponse, SpecMatchRecordListResponse,
    SpecMatchCheckRequest, SpecMatchCheckResponse, SpecMatchResult,
    SpecExtractRequest, SpecExtractResponse
)
from .sales import (
    LeadCreate, LeadUpdate, LeadResponse,
    OpportunityCreate, OpportunityUpdate, OpportunityResponse, OpportunityRequirementResponse,
    GateSubmitRequest,
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteVersionCreate, QuoteVersionResponse,
    QuoteItemResponse, QuoteApproveRequest,
    QuoteCostTemplateCreate, QuoteCostTemplateUpdate, QuoteCostTemplateResponse,
    QuoteCostApprovalCreate, QuoteCostApprovalResponse, QuoteCostApprovalAction,
    CostBreakdownResponse, CostCheckResponse, CostComparisonResponse,
    ContractCreate, ContractUpdate, ContractResponse, ContractDeliverableResponse,
    ContractSignRequest, ContractProjectCreateRequest,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceIssueRequest,
    ReceivableDisputeCreate, ReceivableDisputeUpdate, ReceivableDisputeResponse,
    QuoteApprovalResponse, QuoteApprovalCreate,
    ContractApprovalResponse, ContractApprovalCreate,
    InvoiceApprovalResponse, InvoiceApprovalCreate,
    # Technical Assessment
    TechnicalAssessmentApplyRequest, TechnicalAssessmentEvaluateRequest, TechnicalAssessmentResponse,
    ScoringRuleCreate, ScoringRuleResponse,
    FailureCaseCreate, FailureCaseResponse,
    OpenItemCreate, OpenItemResponse,
    LeadRequirementDetailCreate, LeadRequirementDetailResponse,
    RequirementFreezeCreate, RequirementFreezeResponse,
    AIClarificationCreate, AIClarificationUpdate, AIClarificationResponse
)
from .project_review import (
    ProjectReviewCreate, ProjectReviewUpdate, ProjectReviewResponse,
    ProjectLessonCreate, ProjectLessonUpdate, ProjectLessonResponse,
    ProjectBestPracticeCreate, ProjectBestPracticeUpdate, ProjectBestPracticeResponse,
    LessonStatisticsResponse, BestPracticeRecommendationRequest, BestPracticeRecommendationResponse
)
from .technical_review import (
    TechnicalReviewCreate, TechnicalReviewUpdate, TechnicalReviewResponse, TechnicalReviewDetailResponse,
    ReviewParticipantCreate, ReviewParticipantUpdate, ReviewParticipantResponse,
    ReviewMaterialCreate, ReviewMaterialResponse,
    ReviewChecklistRecordCreate, ReviewChecklistRecordUpdate, ReviewChecklistRecordResponse,
    ReviewIssueCreate, ReviewIssueUpdate, ReviewIssueResponse
)
from .project_role import (
    ProjectRoleTypeBase, ProjectRoleTypeCreate, ProjectRoleTypeUpdate, ProjectRoleTypeResponse, ProjectRoleTypeListResponse,
    ProjectRoleConfigBase, ProjectRoleConfigCreate, ProjectRoleConfigUpdate, ProjectRoleConfigBatchUpdate,
    ProjectRoleConfigResponse, ProjectRoleConfigListResponse,
    ProjectLeadCreate, ProjectLeadUpdate, ProjectLeadResponse, ProjectLeadListResponse,
    TeamMemberCreate, TeamMemberResponse, TeamMemberListResponse,
    ProjectLeadWithTeamResponse, ProjectRoleOverviewResponse, UserBrief
)
from .assembly_kit import (
    # Assembly Stage
    AssemblyStageCreate, AssemblyStageUpdate, AssemblyStageResponse,
    # Assembly Template
    AssemblyTemplateCreate, AssemblyTemplateUpdate, AssemblyTemplateResponse,
    # Category Stage Mapping
    CategoryStageMappingCreate, CategoryStageMappingUpdate, CategoryStageMappingResponse,
    # BOM Assembly Attrs
    BomItemAssemblyAttrsCreate, BomItemAssemblyAttrsBatchCreate, BomItemAssemblyAttrsUpdate, BomItemAssemblyAttrsResponse,
    BomAssemblyAttrsAutoRequest, BomAssemblyAttrsTemplateRequest,
    # Material Readiness
    MaterialReadinessCreate, MaterialReadinessResponse, MaterialReadinessDetailResponse, StageKitRate,
    # Shortage Detail
    ShortageDetailResponse, ShortageAlertItem, ShortageAlertListResponse,
    # Shortage Alert Rule
    ShortageAlertRuleCreate, ShortageAlertRuleUpdate, ShortageAlertRuleResponse,
    # Scheduling Suggestion
    SchedulingSuggestionResponse, SchedulingSuggestionAccept, SchedulingSuggestionReject,
    # Dashboard
    AssemblyDashboardResponse, AssemblyDashboardStats, AssemblyDashboardStageStats,
    AssemblyKitListResponse
)

__all__ = [
    # Common
    'ResponseModel', 'PaginatedResponse', 'PageParams',
    'IdResponse', 'MessageResponse', 'StatusUpdate',
    # Auth
    'Token', 'TokenData', 'LoginRequest', 'UserCreate', 'UserUpdate', 'UserResponse', 'UserRoleAssign',
    # Project
    'ProjectCreate', 'ProjectUpdate', 'ProjectResponse', 'ProjectListResponse',
    'MachineCreate', 'MachineUpdate', 'MachineResponse',
    'MilestoneCreate', 'MilestoneUpdate', 'MilestoneResponse',
    # Material
    'MaterialCreate', 'MaterialUpdate', 'MaterialResponse',
    'SupplierCreate', 'SupplierUpdate', 'SupplierResponse',
    'BomCreate', 'BomItemCreate', 'BomResponse',
    # Purchase
    'PurchaseOrderCreate', 'PurchaseOrderUpdate', 'PurchaseOrderResponse',
    'PurchaseOrderItemCreate', 'GoodsReceiptCreate',
    # ECN
    'EcnCreate', 'EcnUpdate', 'EcnResponse',
    'EcnEvaluationCreate', 'EcnApprovalCreate', 'EcnTaskCreate',
    # Acceptance
    'AcceptanceOrderCreate', 'AcceptanceOrderUpdate', 'AcceptanceOrderResponse',
    'CheckItemResultUpdate', 'AcceptanceIssueCreate',
    # Outsourcing
    'VendorCreate', 'VendorUpdate', 'VendorResponse',
    'OutsourcingOrderCreate', 'OutsourcingOrderUpdate', 'OutsourcingOrderResponse',
    # Alert
    'AlertRuleCreate', 'AlertRuleUpdate', 'AlertRuleResponse',
    'AlertRecordResponse', 'ExceptionEventCreate', 'ExceptionEventResponse',
    # Technical Spec
    'TechnicalSpecRequirementCreate', 'TechnicalSpecRequirementUpdate', 'TechnicalSpecRequirementResponse',
    'TechnicalSpecRequirementListResponse', 'SpecMatchRecordResponse', 'SpecMatchRecordListResponse',
    'SpecMatchCheckRequest', 'SpecMatchCheckResponse', 'SpecMatchResult',
    'SpecExtractRequest', 'SpecExtractResponse',
    # Sales
    'LeadCreate', 'LeadUpdate', 'LeadResponse',
    'OpportunityCreate', 'OpportunityUpdate', 'OpportunityResponse', 'OpportunityRequirementResponse',
    'GateSubmitRequest',
    'QuoteCreate', 'QuoteUpdate', 'QuoteResponse', 'QuoteVersionCreate', 'QuoteVersionResponse',
    'QuoteItemResponse', 'QuoteApproveRequest',
    'QuoteCostTemplateCreate', 'QuoteCostTemplateUpdate', 'QuoteCostTemplateResponse',
    'QuoteCostApprovalCreate', 'QuoteCostApprovalResponse', 'QuoteCostApprovalAction',
    'CostBreakdownResponse', 'CostCheckResponse', 'CostComparisonResponse',
    'ContractCreate', 'ContractUpdate', 'ContractResponse', 'ContractDeliverableResponse',
    'ContractSignRequest', 'ContractProjectCreateRequest',
    'InvoiceCreate', 'InvoiceUpdate', 'InvoiceResponse', 'InvoiceIssueRequest',
    'ReceivableDisputeCreate', 'ReceivableDisputeUpdate', 'ReceivableDisputeResponse',
    'QuoteApprovalResponse', 'QuoteApprovalCreate',
    'ContractApprovalResponse', 'ContractApprovalCreate',
    'InvoiceApprovalResponse', 'InvoiceApprovalCreate',
    # Technical Assessment
    'TechnicalAssessmentApplyRequest', 'TechnicalAssessmentEvaluateRequest', 'TechnicalAssessmentResponse',
    'ScoringRuleCreate', 'ScoringRuleResponse',
    'FailureCaseCreate', 'FailureCaseResponse',
    'OpenItemCreate', 'OpenItemResponse',
    'LeadRequirementDetailCreate', 'LeadRequirementDetailResponse',
    'RequirementFreezeCreate', 'RequirementFreezeResponse',
    'AIClarificationCreate', 'AIClarificationUpdate', 'AIClarificationResponse',
    # Project Review
    'ProjectReviewCreate', 'ProjectReviewUpdate', 'ProjectReviewResponse',
    'ProjectLessonCreate', 'ProjectLessonUpdate', 'ProjectLessonResponse',
    'ProjectBestPracticeCreate', 'ProjectBestPracticeUpdate', 'ProjectBestPracticeResponse',
    'LessonStatisticsResponse', 'BestPracticeRecommendationRequest', 'BestPracticeRecommendationResponse',
    # Technical Review
    'TechnicalReviewCreate', 'TechnicalReviewUpdate', 'TechnicalReviewResponse', 'TechnicalReviewDetailResponse',
    'ReviewParticipantCreate', 'ReviewParticipantUpdate', 'ReviewParticipantResponse',
    'ReviewMaterialCreate', 'ReviewMaterialResponse',
    'ReviewChecklistRecordCreate', 'ReviewChecklistRecordUpdate', 'ReviewChecklistRecordResponse',
    'ReviewIssueCreate', 'ReviewIssueUpdate', 'ReviewIssueResponse',
    # Assembly Kit Analysis
    'AssemblyStageCreate', 'AssemblyStageUpdate', 'AssemblyStageResponse',
    'AssemblyTemplateCreate', 'AssemblyTemplateUpdate', 'AssemblyTemplateResponse',
    'CategoryStageMappingCreate', 'CategoryStageMappingUpdate', 'CategoryStageMappingResponse',
    'BomItemAssemblyAttrsCreate', 'BomItemAssemblyAttrsBatchCreate', 'BomItemAssemblyAttrsUpdate', 'BomItemAssemblyAttrsResponse',
    'BomAssemblyAttrsAutoRequest', 'BomAssemblyAttrsTemplateRequest',
    'MaterialReadinessCreate', 'MaterialReadinessResponse', 'MaterialReadinessDetailResponse', 'StageKitRate',
    'ShortageDetailResponse', 'ShortageAlertItem', 'ShortageAlertListResponse',
    'ShortageAlertRuleCreate', 'ShortageAlertRuleUpdate', 'ShortageAlertRuleResponse',
    'SchedulingSuggestionResponse', 'SchedulingSuggestionAccept', 'SchedulingSuggestionReject',
    'AssemblyDashboardResponse', 'AssemblyDashboardStats', 'AssemblyDashboardStageStats',
    'AssemblyKitListResponse',
    # Project Role Config
    'ProjectRoleTypeBase', 'ProjectRoleTypeCreate', 'ProjectRoleTypeUpdate', 'ProjectRoleTypeResponse', 'ProjectRoleTypeListResponse',
    'ProjectRoleConfigBase', 'ProjectRoleConfigCreate', 'ProjectRoleConfigUpdate', 'ProjectRoleConfigBatchUpdate',
    'ProjectRoleConfigResponse', 'ProjectRoleConfigListResponse',
    'ProjectLeadCreate', 'ProjectLeadUpdate', 'ProjectLeadResponse', 'ProjectLeadListResponse',
    'TeamMemberCreate', 'TeamMemberResponse', 'TeamMemberListResponse',
    'ProjectLeadWithTeamResponse', 'ProjectRoleOverviewResponse', 'UserBrief',
]
