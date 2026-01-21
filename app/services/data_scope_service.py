# -*- coding: utf-8 -*-
"""
数据权限服务
实现基于角色的数据权限过滤

注意：此文件已拆分为多个模块文件，位于 data_scope/ 目录下
此文件仅用于向后兼容，重新导出所有接口
"""

# 从拆分后的模块重新导出所有接口
from .data_scope import (
    DataScopeConfig,
    DATA_SCOPE_CONFIGS,
    DataScopeService,
    UserScopeService,
    ProjectFilterService,
    IssueFilterService,
    GenericFilterService,
)

__all__ = [
    "DataScopeConfig",
    "DATA_SCOPE_CONFIGS",
    "DataScopeService",
    "UserScopeService",
    "ProjectFilterService",
    "IssueFilterService",
    "GenericFilterService",
]
