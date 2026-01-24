# -*- coding: utf-8 -*-
"""
项目里程碑 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
"""

from fastapi import APIRouter, Path, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.core import security
from app.models.project import ProjectMilestone
from app.models.user import User
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)


def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(ProjectMilestone.status == status)


# 使用项目中心CRUD路由基类创建路由
router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id",
    keyword_fields=["milestone_name", "milestone_code", "description"],
    default_order_by="planned_date",
    default_order_direction="desc",
    custom_filters={
        "status": filter_by_status  # 支持 ?status=PENDING 筛选
    }
)
