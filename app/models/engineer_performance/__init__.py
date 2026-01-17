# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 - 模型聚合层
"""

from .common import (
    CollaborationRating,
    EngineerDimensionConfig,
    EngineerProfile,
    KnowledgeContribution,
    KnowledgeReuseLog,
)
from .electrical import (
    ComponentSelection,
    ElectricalDrawingVersion,
    ElectricalFaultRecord,
    PlcModuleLibrary,
    PlcProgramVersion,
)
from .enums import (
    BugFoundStageEnum,
    CodeModuleCategoryEnum,
    ContributionStatusEnum,
    ContributionTypeEnum,
    DrawingTypeEnum,
    EngineerJobLevelEnum,
    EngineerJobTypeEnum,
    IssueSeverityEnum,
    IssueStatusEnum,
    PlcBrandEnum,
    PlcModuleCategoryEnum,
    ReviewResultEnum,
)
from .mechanical import (
    DesignReuseRecord,
    DesignReview,
    MechanicalDebugIssue,
)
from .test import (
    CodeModule,
    CodeReviewRecord,
    TestBugRecord,
)

__all__ = [
    # Enums
    'EngineerJobTypeEnum',
    'EngineerJobLevelEnum',
    'ContributionTypeEnum',
    'ContributionStatusEnum',
    'ReviewResultEnum',
    'IssueSeverityEnum',
    'IssueStatusEnum',
    'BugFoundStageEnum',
    'PlcBrandEnum',
    'DrawingTypeEnum',
    'CodeModuleCategoryEnum',
    'PlcModuleCategoryEnum',
    # Common Models
    'EngineerProfile',
    'EngineerDimensionConfig',
    'CollaborationRating',
    'KnowledgeContribution',
    'KnowledgeReuseLog',
    # Mechanical Models
    'DesignReview',
    'MechanicalDebugIssue',
    'DesignReuseRecord',
    # Test Models
    'TestBugRecord',
    'CodeReviewRecord',
    'CodeModule',
    # Electrical Models
    'ElectricalDrawingVersion',
    'PlcProgramVersion',
    'PlcModuleLibrary',
    'ComponentSelection',
    'ElectricalFaultRecord',
]
