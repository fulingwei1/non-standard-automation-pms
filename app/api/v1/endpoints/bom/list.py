# -*- coding: utf-8 -*-
"""
BOM列表查询 - 从 bom.py 拆分
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import BomHeader
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.material import BomResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[BomResponse])
def list_boms(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量",
    ),
    project_id: Optional[int] = Query(
        None, alias="project", description="按项目ID筛选"
    ),
    machine_id: Optional[int] = Query(None, description="按机台ID筛选"),
    is_latest: Optional[bool] = Query(None, description="只返回最新版本"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取BOM列表（支持分页和筛选）
    """
    query = db.query(BomHeader).options(
        joinedload(BomHeader.project),
        joinedload(BomHeader.machine),
    )

    if project_id:
        query = query.filter(BomHeader.project_id == project_id)
    if machine_id:
        query = query.filter(BomHeader.machine_id == machine_id)
    if is_latest is not None:
        query = query.filter(BomHeader.is_latest == is_latest)

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    boms = (
        query.order_by(BomHeader.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # 分页计算
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=[BomResponse.model_validate(b) for b in boms],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
