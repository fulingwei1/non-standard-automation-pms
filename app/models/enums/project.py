# -*- coding: utf-8 -*-
"""
项目相关枚举
"""
from enum import Enum


class ProjectStageEnum(str, Enum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
    S5 = "S5"
    S6 = "S6"
    S7 = "S7"
    S8 = "S8"
    S9 = "S9"


class ProjectHealthEnum(str, Enum):
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"


class MachineStatusEnum(str, Enum):
    DESIGN = "DESIGN"
    PROCUREMENT = "PROCUREMENT"
    ASSEMBLY = "ASSEMBLY"
    DEBUGGING = "DEBUGGING"
    TESTING = "TESTING"
    FAT_PASSED = "FAT_PASSED"
    SHIPPED = "SHIPPED"
    SAT_PASSED = "SAT_PASSED"
    ACCEPTED = "ACCEPTED"


class MilestoneTypeEnum(str, Enum):
    KICKOFF = "KICKOFF"
    DESIGN_REVIEW = "DESIGN_REVIEW"
    PROCUREMENT_COMPLETE = "PROCUREMENT_COMPLETE"
    ASSEMBLY_COMPLETE = "ASSEMBLY_COMPLETE"
    FAT = "FAT"
    SHIPMENT = "SHIPMENT"
    SAT = "SAT"
    FINAL_ACCEPTANCE = "FINAL_ACCEPTANCE"


class ProjectNoveltyLevelEnum(str, Enum):
    STANDARD = "STANDARD"
    MODIFIED = "MODIFIED"
    NEW = "NEW"


class ProjectEvaluationLevelEnum(str, Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class ProjectEvaluationStatusEnum(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatusEnum(str, Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class TaskImportance(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class TaskPriority(str, Enum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class AssemblyStageEnum(str, Enum):
    DESIGN = "DESIGN"
    PROCUREMENT = "PROCUREMENT"
    FABRICATION = "FABRICATION"
    ASSEMBLY = "ASSEMBLY"
    DEBUGGING = "DEBUGGING"
    TESTING = "TESTING"
    PACKAGING = "PACKAGING"
    SHIPPED = "SHIPPED"
