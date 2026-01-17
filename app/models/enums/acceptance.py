# -*- coding: utf-8 -*-
"""
验收和质量相关枚举
"""
from enum import Enum


class AcceptanceTypeEnum(str, Enum):
    FAT = "FAT"
    SAT = "SAT"
    FINAL = "FINAL"


class AcceptanceOrderStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AcceptanceResultEnum(str, Enum):
    PASS = "PASS"  # nosec B105
    CONDITIONAL_PASS = "CONDITIONAL_PASS"  # nosec B105
    FAIL = "FAIL"


class CheckItemResultEnum(str, Enum):
    PASS = "PASS"  # nosec B105
    FAIL = "FAIL"
    NA = "NA"


class IssueTypeEnum(str, Enum):
    DEFECT = "DEFECT"
    RISK = "RISK"
    BLOCKER = "BLOCKER"
    OTHER = "OTHER"


class SeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class IssueStatusEnum(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class IssueRootCauseEnum(str, Enum):
    DESIGN_ERROR = "DESIGN_ERROR"
    MATERIAL_DEFECT = "MATERIAL_DEFECT"
    PROCESS_ERROR = "PROCESS_ERROR"
    EXTERNAL_FACTOR = "EXTERNAL_FACTOR"
    OTHER = "OTHER"


class VendorTypeEnum(str, Enum):
    DESIGN = "DESIGN"
    MANUFACTURING = "MANUFACTURING"
    SERVICE = "SERVICE"


class OutsourcingOrderStatusEnum(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InspectionResultEnum(str, Enum):
    PASS = "PASS"  # nosec B105
    CONDITIONAL_PASS = "CONDITIONAL_PASS"  # nosec B105
    FAIL = "FAIL"


class DispositionEnum(str, Enum):
    ACCEPT = "ACCEPT"
    REWORK = "REWORK"
    SCRAP = "SCRAP"
    RETURN = "RETURN"
    QUARANTINE = "QUARANTINE"
