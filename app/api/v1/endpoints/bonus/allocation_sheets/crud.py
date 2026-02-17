# -*- coding: utf-8 -*-
"""
奖金分配明细表 - CRUD操作
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.bonus import BonusAllocationSheet
from app.models.user import User
from app.schemas.bonus import BonusAllocationSheetResponse
from app.schemas.common import ResponseModel
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


@router.get("/allocation-sheets", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_allocation_sheets(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    sheet_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取分配明细表列表
    """
    query = db.query(BonusAllocationSheet)

    if sheet_status:
        query = query.filter(BonusAllocationSheet.status == sheet_status)

    total = query.count()
    sheets = apply_pagination(query.order_by(desc(BonusAllocationSheet.created_at)), pagination.offset, pagination.limit).all()

    items = [BonusAllocationSheetResponse.model_validate(sheet) for sheet in sheets]

    return ResponseModel(
        code=200,
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pagination.pages_for_total(total)
        }
    )


@router.get("/allocation-sheets/{sheet_id}", response_model=ResponseModel[BonusAllocationSheetResponse], status_code=status.HTTP_200_OK)
def get_allocation_sheet(
    *,
    db: Session = Depends(deps.get_db),
    sheet_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取分配明细表详情
    """
    sheet = get_or_404(db, BonusAllocationSheet, sheet_id, "分配明细表不存在")

    return ResponseModel(
        code=200,
        data=BonusAllocationSheetResponse.model_validate(sheet)
    )
