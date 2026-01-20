# -*- coding: utf-8 -*-
"""
审批和工作流相关枚举
"""

from enum import Enum


class BonusTypeEnum(str, Enum):
    PROJECT_BONUS = "PROJECT_BONUS"
    PERFORMANCE_BONUS = "PERFORMANCE_BONUS"
    SALES_BONUS = "SALES_BONUS"
    TEAM_BONUS = "TEAM_BONUS"


class BonusCalculationStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class BonusDistributionStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PaymentMethodEnum(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHECK = "CHECK"


class TeamBonusAllocationMethodEnum(str, Enum):
    EQUAL = "EQUAL"
    PERFORMANCE_BASED = "PERFORMANCE_BASED"
    CUSTOM = "CUSTOM"


class EcnTypeEnum(str, Enum):
    DESIGN_CHANGE = "DESIGN_CHANGE"
    MATERIAL_CHANGE = "MATERIAL_CHANGE"
    PROCESS_CHANGE = "PROCESS_CHANGE"
    SPEC_CHANGE = "SPEC_CHANGE"
    PLAN_CHANGE = "PLAN_CHANGE"
    OTHER = "OTHER"


class EcnSourceTypeEnum(str, Enum):
    CUSTOMER = "CUSTOMER"
    INTERNAL = "INTERNAL"
    SUPPLIER = "SUPPLIER"


class EcnStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"
    CANCELLED = "CANCELLED"


class PriorityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ChangeScopeEnum(str, Enum):
    DESIGN = "DESIGN"
    MATERIAL = "MATERIAL"
    PROCESS = "PROCESS"
    SCHEDULE = "SCHEDULE"
    COST = "COST"


class WorkflowTypeEnum(str, Enum):
    QUOTE = "QUOTE"
    CONTRACT = "CONTRACT"
    INVOICE = "INVOICE"
    ECN = "ECN"
    OTHER = "OTHER"


class ApprovalRecordStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ApprovalActionEnum(str, Enum):
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    WITHDRAW = "WITHDRAW"
    DELEGATE = "DELEGATE"


class NotifyChannelEnum(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WEB = "WEB"
    MOBILE_APP = "MOBILE_APP"


class EcnChangeTypeEnum(str, Enum):
    """ECN变更类型枚举（兼容层，值与EcnTypeEnum一致）"""

    DESIGN = "DESIGN_CHANGE"
    MATERIAL = "MATERIAL_CHANGE"
    PROCESS = "PROCESS_CHANGE"
    SPEC = "SPEC_CHANGE"
    PLAN = "PLAN_CHANGE"
