# -*- coding: utf-8 -*-
"""
年度重点工作服务模块

聚合所有年度重点工作相关的服务函数，保持向后兼容
"""
from .crud import (
    create_annual_work,
    delete_annual_work,
    get_annual_work,
    list_annual_works,
    update_annual_work,
)
from .detail_stats import (
    get_annual_work_detail,
    get_annual_work_stats,
)
from .progress import (
    calculate_progress_from_projects,
    sync_progress_from_projects,
    update_progress,
)
from .projects import (
    get_linked_projects,
    link_project,
    unlink_project,
)

__all__ = [
    # CRUD
    "create_annual_work",
    "get_annual_work",
    "list_annual_works",
    "update_annual_work",
    "delete_annual_work",
    # 进度管理
    "update_progress",
    "calculate_progress_from_projects",
    "sync_progress_from_projects",
    # 项目关联
    "link_project",
    "unlink_project",
    "get_linked_projects",
    # 详情和统计
    "get_annual_work_detail",
    "get_annual_work_stats",
]
