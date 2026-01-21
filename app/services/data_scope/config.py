# -*- coding: utf-8 -*-
"""
数据权限配置
定义数据权限过滤的配置类和预定义配置
"""

from dataclasses import dataclass
from typing import Callable, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models.user import User


@dataclass
class DataScopeConfig:
    """
    数据权限过滤配置

    用于配置不同模型的数据权限过滤字段映射
    """
    # 所有者字段（用于 OWN 范围）
    owner_field: Optional[str] = "created_by"
    # 额外的所有者字段列表（如 pm_id, assignee_id）
    additional_owner_fields: Optional[List[str]] = None
    # 部门字段（用于 DEPT 范围）- 可以是直接的 dept_id 或通过关联查找
    dept_field: Optional[str] = None
    # 项目关联字段（用于 PROJECT 范围）
    project_field: Optional[str] = "project_id"
    # 是否通过项目间接获取部门（当没有直接 dept_field 时）
    dept_through_project: bool = True
    # 自定义过滤函数（用于复杂场景）
    custom_filter: Optional[Callable[[Query, User, str, Session], Query]] = None


# 预定义的模块数据权限配置
DATA_SCOPE_CONFIGS = {
    "purchase_order": DataScopeConfig(
        owner_field="requester_id",
        additional_owner_fields=["created_by"],
        project_field="project_id",
    ),
    "acceptance_order": DataScopeConfig(
        owner_field="created_by",
        additional_owner_fields=["inspector_id"],
        project_field="project_id",
    ),
    "material_arrival": DataScopeConfig(
        owner_field="created_by",
        project_field="project_id",
    ),
    "material_substitution": DataScopeConfig(
        owner_field="created_by",
        additional_owner_fields=["approved_by"],
        project_field="project_id",
    ),
    "task": DataScopeConfig(
        owner_field="assignee_id",
        additional_owner_fields=["created_by"],
        project_field="project_id",
    ),
    "document": DataScopeConfig(
        owner_field="uploaded_by",
        project_field="project_id",
    ),
    "pitfall": DataScopeConfig(
        owner_field="created_by",
        project_field="project_id",
    ),
}
