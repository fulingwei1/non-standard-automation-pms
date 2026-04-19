# -*- coding: utf-8 -*-
"""向后兼容 re-export：ECN 自动分配服务现位于 app.services.ecn.ecn_auto_assign_service。"""

from app.services.ecn.ecn_auto_assign_service import (  # noqa: F401
    auto_assign_evaluation,
    auto_assign_pending_approvals,
    auto_assign_pending_evaluations,
    auto_assign_pending_tasks,
    find_users_by_department,
    find_users_by_role,
)

__all__ = [
    "find_users_by_department",
    "find_users_by_role",
    "auto_assign_evaluation",
    "auto_assign_pending_evaluations",
    "auto_assign_pending_approvals",
    "auto_assign_pending_tasks",
]
