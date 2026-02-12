# -*- coding: utf-8 -*-
"""
项目成本 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
"""

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.models.project import ProjectCost
from app.schemas.project import (
    ProjectCostCreate,
    ProjectCostUpdate,
    ProjectCostResponse
)


def filter_by_cost_type(query, cost_type: str):
    """自定义成本类型筛选器"""
    return query.filter(ProjectCost.cost_type == cost_type)


# 使用项目中心CRUD路由基类创建路由
router = create_project_crud_router(
    model=ProjectCost,
    create_schema=ProjectCostCreate,
    update_schema=ProjectCostUpdate,
    response_schema=ProjectCostResponse,
    permission_prefix="cost",
    project_id_field="project_id",
    keyword_fields=["description", "source_no", "cost_category"],
    default_order_by="created_at",
    default_order_direction="desc",
    custom_filters={
        "cost_type": filter_by_cost_type  # 支持 ?cost_type=LABOR 筛选
    }
)
