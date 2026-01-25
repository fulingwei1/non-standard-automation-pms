"""
核心基础模型导出模块

包含：
- 基础模型和工具
- 用户、角色、权限
- 项目和客户
- 机器设备
"""

# 基础模型
from ..base import Base, TimestampMixin, get_engine, get_session, init_db

# 用户相关
from ..user import Permission, PermissionAudit, Role, RolePermission, User, UserRole

# 项目相关
from ..project import (
    Customer,
    FinancialProjectCost,
    Machine,
    Project,
    ProjectCost,
    ProjectDocument,
    ProjectMember,
    ProjectMemberContribution,
    ProjectMilestone,
    ProjectPaymentPlan,
    ProjectStage,
)

# 权限V2
from ..permission import (
    DataScopeRule,
    MenuPermission,
    MenuType,
    PermissionGroup,
    PermissionType,
    ResourceType,
    RoleDataScope,
    RoleMenu,
    ScopeType,
)

__all__ = [
    # 基础
    "Base",
    "TimestampMixin",
    "get_engine",
    "get_session",
    "init_db",
    # 用户
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "PermissionAudit",
    # 项目
    "Project",
    "Customer",
    "Machine",
    "ProjectMember",
    "ProjectMilestone",
    "ProjectDocument",
    "ProjectCost",
    "FinancialProjectCost",
    "ProjectMemberContribution",
    "ProjectPaymentPlan",
    "ProjectStage",
    # 权限V2
    "MenuPermission",
    "PermissionGroup",
    "RoleMenu",
    "RoleDataScope",
    "DataScopeRule",
    "MenuType",
    "PermissionType",
    "ResourceType",
    "ScopeType",
]
