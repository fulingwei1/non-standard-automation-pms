# -*- coding: utf-8 -*-
"""
数据权限服务
实现基于角色的数据权限过滤

此模块已拆分为多个子模块：
- config: 配置类和预定义配置
- user_scope: 用户权限范围相关方法
- project_filter: 项目过滤相关方法
- issue_filter: 问题过滤方法
- generic_filter: 通用过滤方法
"""

# 配置
from .config import DataScopeConfig, DATA_SCOPE_CONFIGS

# 用户权限范围服务
from .user_scope import UserScopeService

# 项目过滤服务
from .project_filter import ProjectFilterService

# 问题过滤服务
from .issue_filter import IssueFilterService

# 通用过滤服务
from .generic_filter import GenericFilterService


# 为了向后兼容，创建 DataScopeService 类，聚合所有方法
class DataScopeService:
    """数据权限范围服务 - 向后兼容类"""

    # 用户权限范围方法
    get_user_data_scope = staticmethod(UserScopeService.get_user_data_scope)
    get_user_project_ids = staticmethod(UserScopeService.get_user_project_ids)
    get_subordinate_ids = staticmethod(UserScopeService.get_subordinate_ids)

    # 项目过滤方法
    filter_projects_by_scope = staticmethod(ProjectFilterService.filter_projects_by_scope)
    check_project_access = staticmethod(ProjectFilterService.check_project_access)
    _filter_own_projects = staticmethod(ProjectFilterService._filter_own_projects)

    # 问题过滤方法
    filter_issues_by_scope = staticmethod(IssueFilterService.filter_issues_by_scope)

    # 通用过滤方法
    filter_by_scope = staticmethod(GenericFilterService.filter_by_scope)
    check_customer_access = staticmethod(GenericFilterService.check_customer_access)


# 导出所有公共接口
__all__ = [
    # 配置
    "DataScopeConfig",
    "DATA_SCOPE_CONFIGS",
    # 主服务类（向后兼容）
    "DataScopeService",
    # 子服务类（新接口）
    "UserScopeService",
    "ProjectFilterService",
    "IssueFilterService",
    "GenericFilterService",
]
