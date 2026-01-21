# -*- coding: utf-8 -*-
"""
奖金分配明细表 - CRUD操作
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.bonus import BonusAllocationSheet
from app.models.user import User
from app.schemas.bonus import BonusAllocationSheetResponse
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/allocation-sheets", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_allocation_sheets(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取分配明细表列表
    """
    query = db.query(BonusAllocationSheet)

    if status:
        query = query.filter(BonusAllocationSheet.status == status)

    total = query.count()
    sheets = query.order_by(desc(BonusAllocationSheet.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    items = [BonusAllocationSheetResponse.model_validate(sheet) for sheet in sheets]

    return ResponseModel(
        code=200,
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
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
    sheet = db.query(BonusAllocationSheet).filter(BonusAllocationSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="分配明细表不存在")

    return ResponseModel(
        code=200,
        data=BonusAllocationSheetResponse.model_validate(sheet)
    )
