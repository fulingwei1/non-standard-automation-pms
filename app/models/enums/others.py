# -*- coding: utf-8 -*-
"""
其他枚举
"""
from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ActiveStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ReviewTypeEnum(str, Enum):
    DESIGN_REVIEW = "DESIGN_REVIEW"
    TECHNICAL_REVIEW = "TECHNICAL_REVIEW"
    BID_REVIEW = "BID_REVIEW"
    REQUIREMENT_REVIEW = "REQUIREMENT_REVIEW"


class ReviewStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class MeetingTypeEnum(str, Enum):
    KICKOFF = "KICKOFF"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    DEMO = "DEMO"
    RETROSPECTIVE = "RETROSPECTIVE"
    MILESTONE_REVIEW = "MILESTONE_REVIEW"
    CHANGE_REVIEW = "CHANGE_REVIEW"
    RISK_REVIEW = "RISK_REVIEW"
    CLOSURE = "CLOSURE"
    OTHER = "OTHER"


class ReviewConclusionEnum(str, Enum):
    APPROVED = "APPROVED"
    APPROVED_WITH_COMMENTS = "APPROVED_WITH_COMMENTS"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


class ParticipantRoleEnum(str, Enum):
    ORGANIZER = "ORGANIZER"
    PRESENTER = "PRESENTER"
    ATTENDEE = "ATTENDEE"
    OPTIONAL = "OPTIONAL"


class AttendanceStatusEnum(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class MaterialTypeEnumReview(str, Enum):
    STANDARD = "STANDARD"
    MECHANICAL = "MECHANICAL"
    ELECTRICAL = "ELECTRICAL"
    PNEUMATIC = "PNEUMATIC"


class ChecklistResultEnum(str, Enum):
    PASS = "PASS"  # nosec B105
    FAIL = "FAIL"
    NA = "NA"


class IssueLevelEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewIssueStatusEnum(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    WAIVED = "WAIVED"


class VerifyResultEnum(str, Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"


class AssessmentSourceTypeEnum(str, Enum):
    LEAD = "LEAD"
    OPPORTUNITY = "OPPORTUNITY"


class AssessmentStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AssessmentDecisionEnum(str, Enum):
    RECOMMEND = "RECOMMEND"
    CONDITIONAL = "CONDITIONAL"
    DEFER = "DEFER"
    NOT_RECOMMEND = "NOT_RECOMMEND"


class FreezeTypeEnum(str, Enum):
    INITIAL = "INITIAL"
    MAJOR = "MAJOR"
    FINAL = "FINAL"


class OpenItemTypeEnum(str, Enum):
    TECHNICAL = "TECHNICAL"
    COMMERCIAL = "COMMERCIAL"
    LOGISTICS = "LOGISTICS"
    QUALITY = "QUALITY"
    OTHER = "OTHER"


class OpenItemStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class ResponsiblePartyEnum(str, Enum):
    CUSTOMER = "CUSTOMER"
    INTERNAL = "INTERNAL"
    SUPPLIER = "SUPPLIER"
    THIRD_PARTY = "THIRD_PARTY"


class ImportanceLevelEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EquipmentTypeEnum(str, Enum):
    FCT = "FCT"
    EOL = "EOL"
    BURN_IN = "BURN_IN"
    AUTO_ASSEMBLY = "AUTO_ASSEMBLY"
    TEST_EQUIPMENT = "TEST_EQUIPMENT"
    OTHER = "OTHER"


class MeetingRhythmLevel(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BI_WEEKLY = "BI_WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    STRATEGIC = "STRATEGIC"
    OPERATIONAL = "OPERATIONAL"
    OPERATION = "OPERATION"
    TASK = "TASK"


class MeetingCycleType(str, Enum):
    PLANNED = "PLANNED"
    AD_HOC = "AD_HOC"
    RECURRING = "RECURRING"


class ActionItemStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class RhythmHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    AT_RISK = "AT_RISK"
    UNHEALTHY = "UNHEALTHY"


class DataScopeEnum(str, Enum):
    """
    数据权限范围枚举

    用于角色的 data_scope 字段与 DataScopeService 的过滤逻辑：
    ALL > DEPT > SUBORDINATE > PROJECT > OWN
    """

    ALL = "ALL"
    DEPT = "DEPT"
    SUBORDINATE = "SUBORDINATE"
    PROJECT = "PROJECT"
    OWN = "OWN"


class AlertLevelEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"


class AlertStatusEnum(str, Enum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PROCESSING = "PROCESSING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    IGNORED = "IGNORED"


class AlertRuleTypeEnum(str, Enum):
    QUALITY_ISSUE = "QUALITY_ISSUE"
    MILESTONE_DUE = "MILESTONE_DUE"
    COST_OVERRUN = "COST_OVERRUN"
    SCHEDULE_DELAY = "SCHEDULE_DELAY"
    FINANCIAL = "FINANCIAL"
    SPECIFICATION_MISMATCH = "SPECIFICATION_MISMATCH"
