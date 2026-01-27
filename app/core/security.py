# -*- coding: utf-8 -*-
"""
安全认证模块 - 兼容层

此文件保持向后兼容性，从拆分后的模块导入所有功能。
原有功能已拆分为：
- auth.py: 认证和密码管理
- sales_permissions.py: 销售权限
- permissions.py: 其他权限检查
"""

# 从认证模块导入
from .auth import (
    check_permission,
    create_access_token,
    get_current_active_user,
    get_current_active_superuser,
    get_current_user,
    get_password_hash,
    is_system_admin,
    is_token_revoked,
    oauth2_scheme,
    require_permission,
    revoke_token,
    verify_password,
)

# 从权限模块导入
from .permissions import (
    check_sales_create_permission,
    check_sales_delete_permission,
    check_sales_edit_permission,
    filter_sales_data_by_scope,
    filter_sales_finance_data_by_scope,
    get_sales_data_scope,
    has_finance_access,
    has_hr_access,
    has_machine_document_permission,
    has_machine_document_upload_permission,
    has_procurement_access,
    has_production_access,
    has_rd_project_access,
    has_sales_approval_access,
    has_sales_assessment_access,
    has_scheduler_admin_access,
    has_shortage_report_access,
    has_timesheet_approval_access,
    require_finance_access,
    require_hr_access,
    require_procurement_access,
    require_production_access,
    require_project_access,
    require_rd_project_access,
    require_sales_approval_permission,
    require_sales_assessment_access,
    require_sales_create_permission,
    require_sales_delete_permission,
    require_sales_edit_permission,
    require_scheduler_admin_access,
    require_shortage_report_access,
    require_timesheet_approval_access,
    check_timesheet_approval_permission,
)

__all__ = [
    # 认证相关
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_active_superuser",
    "check_permission",
    "require_permission",
    "is_system_admin",
    "oauth2_scheme",
    "revoke_token",
    "is_token_revoked",
    # 基础权限
    "has_procurement_access",
    "require_procurement_access",
    "has_shortage_report_access",
    "require_shortage_report_access",
    "has_finance_access",
    "require_finance_access",
    "has_production_access",
    "require_production_access",
    "require_project_access",
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
    # 人事权限
    "has_hr_access",
    "require_hr_access",
    "has_timesheet_approval_access",
    "require_timesheet_approval_access",
    "has_scheduler_admin_access",
    "require_scheduler_admin_access",
    "has_rd_project_access",
    "require_rd_project_access",
    "has_machine_document_permission",
    "has_machine_document_upload_permission",
]
