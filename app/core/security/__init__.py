# -*- coding: utf-8 -*-
"""
安全认证模块

本模块提供完整的认证和权限管理功能，包括：
- 基础认证（密码验证、JWT令牌）
- 依赖注入（数据库会话、当前用户）
- 通用权限检查
- 模块访问权限（采购、财务、生产、HR等）
- 销售权限（数据范围、CRUD权限、评估、审批）
- 项目权限（项目访问、研发项目、工时审批、设备文档）
"""

# 基础认证
from .auth import (
    pwd_context,
    oauth2_scheme,
    verify_password,
    get_password_hash,
    create_access_token,
    revoke_token,
    is_token_revoked,
)

# 依赖注入
from .deps import (
    get_db,
    get_current_user,
    get_current_active_user,
)

# 通用权限
from .permissions import (
    check_permission,
    require_permission,
)

# 模块访问权限
from .module_access import (
    has_procurement_access,
    require_procurement_access,
    has_shortage_report_access,
    require_shortage_report_access,
    has_finance_access,
    require_finance_access,
    has_production_access,
    require_production_access,
    has_hr_access,
    require_hr_access,
    has_scheduler_admin_access,
    require_scheduler_admin_access,
)

# 销售权限
from .sales_permissions import (
    get_sales_data_scope,
    filter_sales_data_by_scope,
    filter_sales_finance_data_by_scope,
    check_sales_create_permission,
    check_sales_edit_permission,
    check_sales_delete_permission,
    require_sales_create_permission,
    require_sales_edit_permission,
    require_sales_delete_permission,
    has_sales_assessment_access,
    require_sales_assessment_access,
    has_sales_approval_access,
    check_sales_approval_permission,
    require_sales_approval_permission,
)

# 项目权限
from .project_permissions import (
    check_project_access,
    require_project_access,
    RD_PROJECT_ROLES,
    has_rd_project_access,
    require_rd_project_access,
    has_timesheet_approval_access,
    check_timesheet_approval_permission,
    has_machine_document_permission,
    has_machine_document_upload_permission,
)

# 导出列表
__all__ = [
    # 基础认证
    "pwd_context",
    "oauth2_scheme",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "revoke_token",
    "is_token_revoked",
    # 依赖注入
    "get_db",
    "get_current_user",
    "get_current_active_user",
    # 通用权限
    "check_permission",
    "require_permission",
    # 模块访问权限
    "has_procurement_access",
    "require_procurement_access",
    "has_shortage_report_access",
    "require_shortage_report_access",
    "has_finance_access",
    "require_finance_access",
    "has_production_access",
    "require_production_access",
    "has_hr_access",
    "require_hr_access",
    "has_scheduler_admin_access",
    "require_scheduler_admin_access",
    # 销售权限
    "get_sales_data_scope",
    "filter_sales_data_by_scope",
    "filter_sales_finance_data_by_scope",
    "check_sales_create_permission",
    "check_sales_edit_permission",
    "check_sales_delete_permission",
    "require_sales_create_permission",
    "require_sales_edit_permission",
    "require_sales_delete_permission",
    "has_sales_assessment_access",
    "require_sales_assessment_access",
    "has_sales_approval_access",
    "check_sales_approval_permission",
    "require_sales_approval_permission",
    # 项目权限
    "check_project_access",
    "require_project_access",
    "RD_PROJECT_ROLES",
    "has_rd_project_access",
    "require_rd_project_access",
    "has_timesheet_approval_access",
    "check_timesheet_approval_permission",
    "has_machine_document_permission",
    "has_machine_document_upload_permission",
]
