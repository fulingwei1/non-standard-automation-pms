# -*- coding: utf-8 -*-
"""
物料相关枚举
"""
from enum import Enum



class PerformanceLevelEnum(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    QUALIFIED = "QUALIFIED"
    AVERAGE = "AVERAGE"
    NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT"
    POOR = "POOR"


class MaterialTypeEnum(str, Enum):
    STANDARD = "STANDARD"
    MECHANICAL = "MECHANICAL"
    ELECTRICAL = "ELECTRICAL"
    PNEUMATIC = "PNEUMATIC"
    RAW_MATERIAL = "RAW_MATERIAL"


class MaterialSourceEnum(str, Enum):
    CUSTOM_MADE = "CUSTOM_MADE"
    PURCHASED = "PURCHASED"
    CUSTOMER_PROVIDED = "CUSTOMER_PROVIDED"


class PurchaseOrderStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONFIRMED = "CONFIRMED"
    PARTIAL_RECEIVED = "PARTIAL_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class SupplierLevelEnum(str, Enum):
    STRATEGIC = "STRATEGIC"
    PREFERRED = "PREFERRED"
    APPROVED = "APPROVED"
    TRIAL = "TRIAL"
    BLOCKED = "BLOCKED"


class ShortageAlertLevelEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class ShortageStatusEnum(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class ReadinessStatusEnum(str, Enum):
    NOT_READY = "NOT_READY"
    PARTIAL = "PARTIAL"
    READY = "READY"


class ReadinessAnalysisTypeEnum(str, Enum):
    FULL = "FULL"
    QUICK = "QUICK"


class SuggestionTypeEnum(str, Enum):
    PURCHASE = "PURCHASE"
    FABRICATE = "FABRICATE"
    SUBSTITUTE = "SUBSTITUTE"
    OTHER = "OTHER"


class SuggestionStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"
