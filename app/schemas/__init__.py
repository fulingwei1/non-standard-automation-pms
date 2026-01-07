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
    ContractCreate, ContractUpdate, ContractResponse, ContractDeliverableResponse,
    ContractSignRequest, ContractProjectCreateRequest,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceIssueRequest,
    ReceivableDisputeCreate, ReceivableDisputeUpdate, ReceivableDisputeResponse,
    QuoteApprovalResponse, QuoteApprovalCreate,
    ContractApprovalResponse, ContractApprovalCreate,
    InvoiceApprovalResponse, InvoiceApprovalCreate
)
from .project_review import (
    ProjectReviewCreate, ProjectReviewUpdate, ProjectReviewResponse,
    ProjectLessonCreate, ProjectLessonUpdate, ProjectLessonResponse,
    ProjectBestPracticeCreate, ProjectBestPracticeUpdate, ProjectBestPracticeResponse
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
    'ContractCreate', 'ContractUpdate', 'ContractResponse', 'ContractDeliverableResponse',
    'ContractSignRequest', 'ContractProjectCreateRequest',
    'InvoiceCreate', 'InvoiceUpdate', 'InvoiceResponse', 'InvoiceIssueRequest',
    'ReceivableDisputeCreate', 'ReceivableDisputeUpdate', 'ReceivableDisputeResponse',
    'QuoteApprovalResponse', 'QuoteApprovalCreate',
    'ContractApprovalResponse', 'ContractApprovalCreate',
    'InvoiceApprovalResponse', 'InvoiceApprovalCreate',
    # Project Review
    'ProjectReviewCreate', 'ProjectReviewUpdate', 'ProjectReviewResponse',
    'ProjectLessonCreate', 'ProjectLessonUpdate', 'ProjectLessonResponse',
    'ProjectBestPracticeCreate', 'ProjectBestPracticeUpdate', 'ProjectBestPracticeResponse',
]
