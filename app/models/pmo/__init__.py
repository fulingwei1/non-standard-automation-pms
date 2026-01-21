# -*- coding: utf-8 -*-
"""
PMO模型模块

聚合所有PMO项目管理部相关的模型，保持向后兼容
"""
from .change_risk import PmoChangeRequest, PmoProjectRisk
from .cost_meeting import PmoMeeting, PmoProjectCost
from .enums import (
    ChangeLevelEnum,
    ChangeStatusEnum,
    ChangeTypeEnum,
    InitiationStatusEnum,
    MeetingTypeEnum,
    MilestoneStatusEnum,
    PhaseStatusEnum,
    ProjectLevelEnum,
    ProjectPhaseEnum,
    ResourceAllocationStatusEnum,
    RiskCategoryEnum,
    RiskLevelEnum,
    RiskStatusEnum,
)
from .initiation_phase import PmoProjectInitiation, PmoProjectPhase
from .resource_closure import PmoProjectClosure, PmoResourceAllocation

__all__ = [
    # Enums
    "ProjectLevelEnum",
    "ProjectPhaseEnum",
    "InitiationStatusEnum",
    "PhaseStatusEnum",
    "MilestoneStatusEnum",
    "ChangeTypeEnum",
    "ChangeLevelEnum",
    "ChangeStatusEnum",
    "RiskCategoryEnum",
    "RiskLevelEnum",
    "RiskStatusEnum",
    "MeetingTypeEnum",
    "ResourceAllocationStatusEnum",
    # Initiation and Phase
    "PmoProjectInitiation",
    "PmoProjectPhase",
    # Change and Risk
    "PmoChangeRequest",
    "PmoProjectRisk",
    # Cost and Meeting
    "PmoProjectCost",
    "PmoMeeting",
    # Resource and Closure
    "PmoResourceAllocation",
    "PmoProjectClosure",
]
