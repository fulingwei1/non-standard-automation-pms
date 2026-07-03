# -*- coding: utf-8 -*-
"""
时薪配置管理模块

拆分自原 hourly_rate.py (355行)，按功能域分为：
- crud: 时薪配置CRUD操作
- query: 时薪查询API（获取用户时薪、批量查询、历史记录）
"""

from fastapi import APIRouter
from fastapi import Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.hourly_rate import HourlyRateConfigResponse

from .crud import list_hourly_rate_configs
from .crud import router as crud_router
from .query import router as query_router

router = APIRouter()

# 时薪查询API（先注册 /history 等静态路径，避免与 /{config_id} 冲突）
router.include_router(query_router, tags=["时薪查询"])

# 时薪配置CRUD
router.include_router(crud_router, tags=["时薪配置"])


@router.get("", response_model=PaginatedResponse[HourlyRateConfigResponse], include_in_schema=False)
def list_hourly_rate_configs_no_slash(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    config_type: Optional[str] = Query(None, description="配置类型筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    role_id: Optional[int] = Query(None, description="角色ID筛选"),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
):
    return list_hourly_rate_configs(
        db=db,
        pagination=pagination,
        config_type=config_type,
        user_id=user_id,
        role_id=role_id,
        dept_id=dept_id,
        is_active=is_active,
        current_user=current_user,
    )
