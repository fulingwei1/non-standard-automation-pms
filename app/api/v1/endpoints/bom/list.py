# -*- coding: utf-8 -*-
"""
BOM列表查询
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import BomResponse
from app.services.bom_service import BomService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[BomResponse])
def list_boms(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(
        None, alias="project", description="按项目ID筛选"
    ),
    machine_id: Optional[int] = Query(None, description="按机台ID筛选"),
    is_latest: Optional[bool] = Query(None, description="只返回最新版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取BOM列表（支持分页和筛选）
    """
    service = BomService(db)
    result = service.list_boms(
        page=pagination.page,
        page_size=pagination.page_size,
        project_id=project_id,
        machine_id=machine_id,
        is_latest=is_latest,
    )
    return PaginatedResponse(**result)
