# -*- coding: utf-8 -*-
"""
销售相关枚举
"""
from enum import Enum


class LeadStatusEnum(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    CONVERTED = "CONVERTED"
    LOST = "LOST"


class OpportunityStageEnum(str, Enum):
    DISCOVERY = "DISCOVERY"
    QUALIFICATION = "QUALIFICATION"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"


class GateStatusEnum(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class QuoteStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"


class ContractStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    SIGNED = "SIGNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InvoiceStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ISSUED = "ISSUED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class InvoiceTypeEnum(str, Enum):
    VAT = "VAT"
    SPECIAL = "SPECIAL"
    COMMERCIAL = "COMMERCIAL"


class DisputeStatusEnum(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class DisputeReasonCodeEnum(str, Enum):
    PAYMENT_TERMS = "PAYMENT_TERMS"
    DELIVERY_DELAY = "DELIVERY_DELAY"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    SCOPE_CHANGE = "SCOPE_CHANGE"
    OTHER = "OTHER"


class PresalesLeadStatusEnum(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    ASSESSMENT_IN_PROGRESS = "ASSESSMENT_IN_PROGRESS"
    ASSESSMENT_COMPLETED = "ASSESSMENT_COMPLETED"
    CONVERTED_TO_OPPORTUNITY = "CONVERTED_TO_OPPORTUNITY"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"


class EvaluationDecisionEnum(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    GO_WITH_CONDITIONS = "GO_WITH_CONDITIONS"


class WinProbabilityLevelEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class LeadOutcomeEnum(str, Enum):
    WON = "WON"
    LOST = "LOST"
    ABANDONED = "ABANDONED"
    ON_HOLD = "ON_HOLD"


class LossReasonEnum(str, Enum):
    PRICE = "PRICE"
    COMPETITOR = "COMPETITOR"
    TIMING = "TIMING"
    BUDGET = "BUDGET"
    NO_DECISION = "NO_DECISION"
    OTHER = "OTHER"
