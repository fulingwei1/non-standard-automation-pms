# -*- coding: utf-8 -*-
"""
BOM列表查询
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.material import BomHeader
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import BomResponse
from app.services.bom_service import BomService
from app.services.data_scope.config import DataScopeConfig
from app.services.data_scope.data_scope_service import DataScopeService

router = APIRouter()

# BOM 数据权限配置
BOM_DATA_SCOPE_CONFIG = DataScopeConfig(
    owner_field="created_by",
    additional_owner_fields=["approved_by"],
    project_field="project_id",
)


@router.get("/", response_model=PaginatedResponse[BomResponse])
def list_boms(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, alias="project", description="按项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="按机台ID筛选"),
    is_latest: Optional[bool] = Query(None, description="只返回最新版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取BOM列表（支持分页和筛选，按数据权限过滤）
    """
    query = db.query(BomHeader).options(
        joinedload(BomHeader.project), joinedload(BomHeader.machine)
    )

    # 应用数据权限过滤
    query = DataScopeService.filter_by_scope(
        db, query, BomHeader, current_user, BOM_DATA_SCOPE_CONFIG
    )

    if project_id:
        query = query.filter(BomHeader.project_id == project_id)
    if machine_id:
        query = query.filter(BomHeader.machine_id == machine_id)
    if is_latest is not None:
        query = query.filter(BomHeader.is_latest == is_latest)

    total = query.count()

    service = BomService(db)
    boms = apply_pagination(
        query.order_by(BomHeader.created_at.desc()), pagination.offset, pagination.limit
    ).all()
    items = [service._to_response(bom) for bom in boms]

    return PaginatedResponse(**pagination.to_response(items, total))
