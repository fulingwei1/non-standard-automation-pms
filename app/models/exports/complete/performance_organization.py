# -*- coding: utf-8 -*-
"""
完整模型导出 - 绩效和人员相关
"""

# 用户权限
from ...user import (
    ApiPermission,
    PermissionAudit,
    Role,
    RoleApiPermission,
    User,
    UserRole,
)

# API Key认证
from ...api_key import APIKey

# 用户会话
from ...session import UserSession

# 租户
from ...tenant import Tenant, TenantPlan, TenantStatus

# 组织架构
from ...organization import (
    ContractReminder,
    Department,
    Employee,
    EmployeeContract,
    EmployeeHrProfile,
    HrTransaction,
    SalaryRecord,
)

# 组织架构V2
from ...organization import (
    AssignmentType,
    EmployeeOrgAssignment,
    JobLevel,
    JobLevelCategory,
    OrganizationUnit,
    OrganizationUnitType,
    Position,
    PositionCategory,
    PositionRole,
)

# 绩效管理
from ...performance import (
    EvaluationWeightConfig,
    MonthlyWorkSummary,
    PerformanceAdjustmentHistory,
    PerformanceAppeal,
    PerformanceEvaluation,
    PerformanceEvaluationRecord,
    PerformanceIndicator,
    PerformancePeriod,
    PerformanceRankingSnapshot,
    PerformanceResult,
    ProjectContribution,
)

# 人员匹配
from ...staff_matching import (
    HrAIMatchingLog,
    HrEmployeeProfile,
    HrEmployeeTagEvaluation,
    HrProjectPerformance,
    HrTagDict,
    MesProjectStaffingNeed,
)

# 资格认证
from ...qualification import (
    EmployeeQualification,
    PositionCompetencyModel,
    QualificationAssessment,
    QualificationLevel,
)

# 时薪配置
from ...hourly_rate import HourlyRateConfig

__all__ = [
    # User - 新模型
    "User",
    "Role",
    "ApiPermission",
    "RoleApiPermission",
    "UserRole",
    "PermissionAudit",
    "UserSession",
    "APIKey",  # API Key认证
    # Tenant
    "Tenant",
    "TenantPlan",
    "TenantStatus",
    # Organization
    "Department",
    "Employee",
    "EmployeeHrProfile",
    "HrTransaction",
    "EmployeeContract",
    "ContractReminder",
    "SalaryRecord",
    # Organization V2
    "OrganizationUnit",
    "Position",
    "JobLevel",
    "EmployeeOrgAssignment",
    "PositionRole",
    "OrganizationUnitType",
    "PositionCategory",
    "JobLevelCategory",
    "AssignmentType",
    # Performance
    "PerformancePeriod",
    "PerformanceIndicator",
    "PerformanceResult",
    "PerformanceEvaluation",
    "PerformanceAppeal",
    "ProjectContribution",
    "PerformanceRankingSnapshot",
    "PerformanceAdjustmentHistory",
    "MonthlyWorkSummary",
    "PerformanceEvaluationRecord",
    "EvaluationWeightConfig",
    # Staff Matching
    "HrTagDict",
    "HrEmployeeTagEvaluation",
    "HrEmployeeProfile",
    "HrProjectPerformance",
    "MesProjectStaffingNeed",
    "HrAIMatchingLog",
    # Qualification
    "QualificationLevel",
    "PositionCompetencyModel",
    "EmployeeQualification",
    "QualificationAssessment",
    # Hourly Rate
    "HourlyRateConfig",
]
