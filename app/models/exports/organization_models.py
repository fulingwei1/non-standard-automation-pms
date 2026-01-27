# -*- coding: utf-8 -*-
"""
组织相关模型导出
"""

from ..organization import (
    ContractReminder,
    Department,
    Employee,
    EmployeeContract,
    EmployeeHrProfile,
    HrTransaction,
    SalaryRecord,
)
from ..organization import (
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
from ..user import (
    ApiPermission,
    Permission,
    PermissionAudit,
    Role,
    RoleApiPermission,
    RolePermission,
    User,
    UserRole,
)

__all__ = [
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
    # User
    "User",
    "Role",
    "Permission",  # 旧模型
    "UserRole",
    "RolePermission",  # 旧模型
    "ApiPermission",  # 新模型
    "RoleApiPermission",  # 新模型
    "PermissionAudit",
]
