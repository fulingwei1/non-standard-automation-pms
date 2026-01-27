# -*- coding: utf-8 -*-
"""
权限检查模块 - 统一导出
包含：采购、财务、生产、项目、人事、工时、调度器、研发项目、机台文档等权限

向后兼容：保持原有的函数接口
"""

from .finance import (
    has_finance_access,
    require_finance_access,
)
from .hr import (
    has_hr_access,
    require_hr_access,
)
from .machine import (
    has_machine_document_permission,
    has_machine_document_upload_permission,
)
from .procurement import (
    has_procurement_access,
    has_shortage_report_access,
    require_procurement_access,
    require_shortage_report_access,
)
from .production import (
    has_production_access,
    require_production_access,
)
from .project import (
    check_project_access,
    require_project_access,
)
from .rd_project import (
    RD_PROJECT_ROLES,
    has_rd_project_access,
    require_rd_project_access,
)
from .scheduler import (
    has_scheduler_admin_access,
    require_scheduler_admin_access,
)
from .timesheet import (
    check_timesheet_approval_permission,
    has_timesheet_approval_access,
    require_timesheet_approval_access,
)

# 向后兼容：导出所有原有函数和常量
__all__ = [
    # 采购权限
    "has_procurement_access",
    "require_procurement_access",
    "has_shortage_report_access",
    "require_shortage_report_access",
    # 财务权限
    "has_finance_access",
    "require_finance_access",
    # 生产权限
    "has_production_access",
    "require_production_access",
    # 项目权限
    "check_project_access",
    "require_project_access",
    # 人力资源权限
    "has_hr_access",
    "require_hr_access",
    # 工时权限
    "has_timesheet_approval_access",
    "require_timesheet_approval_access",
    "check_timesheet_approval_permission",
    # 调度器权限
    "has_scheduler_admin_access",
    "require_scheduler_admin_access",
    # 研发项目权限
    "RD_PROJECT_ROLES",
    "has_rd_project_access",
    "require_rd_project_access",
    # 机台文档权限
    "has_machine_document_permission",
    "has_machine_document_upload_permission",
]
