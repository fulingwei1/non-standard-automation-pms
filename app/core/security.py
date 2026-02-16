# -*- coding: utf-8 -*-
"""
安全认证模块 - 简化版

权限系统已迁移到数据库驱动模式。
使用 require_permission("module:action") 代替旧的 require_*_access() 函数。
"""

# 从认证模块导入
from .auth import (
    check_permission,
    create_access_token,
    create_token_pair,  # Token刷新功能
    extract_jti_from_token,  # 从token提取JTI
    get_current_active_superuser,
    get_current_active_user,
    get_current_user,
    get_password_hash,
    is_system_admin,
    is_token_revoked,
    oauth2_scheme,
    pwd_context,
    require_permission,
    revoke_token,
    verify_password,
    verify_refresh_token,  # 验证refresh token
)

# 从销售权限模块导入
from .sales_permissions import (
    check_sales_approval_permission,
    check_sales_create_permission,
    check_sales_delete_permission,
    check_sales_edit_permission,
    filter_sales_data_by_scope,
    filter_sales_finance_data_by_scope,
    get_sales_data_scope,
    has_sales_approval_access,
    has_sales_assessment_access,
    require_sales_approval_permission,
    require_sales_assessment_access,
    require_sales_create_permission,
    require_sales_delete_permission,
    require_sales_edit_permission,
)

__all__ = [
    # 认证相关
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_token_pair",  # Token刷新功能
    "verify_refresh_token",  # 验证refresh token
    "extract_jti_from_token",  # 从token提取JTI
    "get_current_user",
    "get_current_active_user",
    "get_current_active_superuser",
    "check_permission",
    "require_permission",
    "is_system_admin",
    "oauth2_scheme",
    "pwd_context",
    "revoke_token",
    "is_token_revoked",
    # 销售权限
    "has_sales_assessment_access",
    "require_sales_assessment_access",
    "get_sales_data_scope",
    "filter_sales_data_by_scope",
    "filter_sales_finance_data_by_scope",
    "check_sales_create_permission",
    "check_sales_edit_permission",
    "check_sales_delete_permission",
    "require_sales_create_permission",
    "require_sales_edit_permission",
    "require_sales_delete_permission",
    "has_sales_approval_access",
    "require_sales_approval_permission",
    "check_sales_approval_permission",
]
