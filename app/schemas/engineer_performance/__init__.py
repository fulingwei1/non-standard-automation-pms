# -*- coding: utf-8 -*-
"""
工程师绩效评价 Schema 模块统一导出

模块结构:
 ├── constants.py         # 枚举值常量
 ├── profile.py           # 工程师档案 Schemas
 ├── dimension_config.py  # 五维配置 Schemas
 ├── collaboration.py     # 跨部门协作 Schemas
 ├── knowledge.py         # 知识贡献 Schemas
 ├── design_review.py     # 设计评审 Schemas
 ├── debug_issue.py       # 调试问题 Schemas
 ├── bug_record.py        # Bug记录 Schemas
 ├── code_module.py       # 代码模块 Schemas
 ├── plc_program.py       # PLC程序 Schemas
 ├── plc_module.py        # PLC模块库 Schemas
 ├── summary.py           # 绩效汇总 Schemas
 └── calculate_task.py    # 计算任务 Schemas
"""

# 枚举值常量
from .constants import (
    BUG_FOUND_STAGES,
    CONTRIBUTION_STATUSES,
    CONTRIBUTION_TYPES,
    ISSUE_SEVERITIES,
    ISSUE_STATUSES,
    JOB_LEVELS,
    JOB_TYPES,
    PLC_BRANDS,
    REVIEW_RESULTS,
)

# 工程师档案
from .profile import (
    EngineerProfileBase,
    EngineerProfileCreate,
    EngineerProfileResponse,
    EngineerProfileUpdate,
)

# 五维配置
from .dimension_config import (
    DimensionConfigBase,
    DimensionConfigCreate,
    DimensionConfigResponse,
    DimensionConfigUpdate,
)

# 跨部门协作
from .collaboration import (
    CollaborationMatrixResponse,
    CollaborationRatingBase,
    CollaborationRatingCreate,
    CollaborationRatingResponse,
)

# 知识贡献
from .knowledge import (
    KnowledgeContributionBase,
    KnowledgeContributionCreate,
    KnowledgeContributionResponse,
    KnowledgeContributionUpdate,
    KnowledgeReuseCreate,
)

# 设计评审
from .design_review import (
    DesignReviewBase,
    DesignReviewCreate,
    DesignReviewResponse,
    DesignReviewUpdate,
)

# 调试问题
from .debug_issue import (
    MechanicalDebugIssueBase,
    MechanicalDebugIssueCreate,
    MechanicalDebugIssueResponse,
    MechanicalDebugIssueUpdate,
)

# Bug记录
from .bug_record import (
    TestBugRecordBase,
    TestBugRecordCreate,
    TestBugRecordResponse,
    TestBugRecordUpdate,
)

# 代码模块
from .code_module import (
    CodeModuleBase,
    CodeModuleCreate,
    CodeModuleResponse,
    CodeModuleUpdate,
)

# PLC程序
from .plc_program import (
    PlcProgramVersionBase,
    PlcProgramVersionCreate,
    PlcProgramVersionResponse,
    PlcProgramVersionUpdate,
)

# PLC模块库
from .plc_module import (
    PlcModuleLibraryBase,
    PlcModuleLibraryCreate,
    PlcModuleLibraryResponse,
    PlcModuleLibraryUpdate,
)

# 绩效汇总
from .summary import (
    CompanySummaryResponse,
    EngineerComparisonResponse,
    EngineerDimensionScore,
    EngineerPerformanceSummary,
    EngineerTrendResponse,
    RankingQueryParams,
    RankingResponse,
)

# 计算任务
from .calculate_task import (
    CalculateTaskCreate,
    CalculateTaskStatus,
)

__all__ = [
    # 枚举值常量
    "JOB_TYPES",
    "JOB_LEVELS",
    "CONTRIBUTION_TYPES",
    "CONTRIBUTION_STATUSES",
    "REVIEW_RESULTS",
    "ISSUE_SEVERITIES",
    "ISSUE_STATUSES",
    "BUG_FOUND_STAGES",
    "PLC_BRANDS",
    # 工程师档案
    "EngineerProfileBase",
    "EngineerProfileCreate",
    "EngineerProfileUpdate",
    "EngineerProfileResponse",
    # 五维配置
    "DimensionConfigBase",
    "DimensionConfigCreate",
    "DimensionConfigUpdate",
    "DimensionConfigResponse",
    # 跨部门协作
    "CollaborationRatingBase",
    "CollaborationRatingCreate",
    "CollaborationRatingResponse",
    "CollaborationMatrixResponse",
    # 知识贡献
    "KnowledgeContributionBase",
    "KnowledgeContributionCreate",
    "KnowledgeContributionUpdate",
    "KnowledgeContributionResponse",
    "KnowledgeReuseCreate",
    # 设计评审
    "DesignReviewBase",
    "DesignReviewCreate",
    "DesignReviewUpdate",
    "DesignReviewResponse",
    # 调试问题
    "MechanicalDebugIssueBase",
    "MechanicalDebugIssueCreate",
    "MechanicalDebugIssueUpdate",
    "MechanicalDebugIssueResponse",
    # Bug记录
    "TestBugRecordBase",
    "TestBugRecordCreate",
    "TestBugRecordUpdate",
    "TestBugRecordResponse",
    # 代码模块
    "CodeModuleBase",
    "CodeModuleCreate",
    "CodeModuleUpdate",
    "CodeModuleResponse",
    # PLC程序
    "PlcProgramVersionBase",
    "PlcProgramVersionCreate",
    "PlcProgramVersionUpdate",
    "PlcProgramVersionResponse",
    # PLC模块库
    "PlcModuleLibraryBase",
    "PlcModuleLibraryCreate",
    "PlcModuleLibraryUpdate",
    "PlcModuleLibraryResponse",
    # 绩效汇总
    "EngineerDimensionScore",
    "EngineerPerformanceSummary",
    "CompanySummaryResponse",
    "RankingQueryParams",
    "RankingResponse",
    "EngineerTrendResponse",
    "EngineerComparisonResponse",
    # 计算任务
    "CalculateTaskCreate",
    "CalculateTaskStatus",
]
