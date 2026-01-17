# -*- coding: utf-8 -*-
"""
BOM生成PR - 从 bom.py 拆分
TODO: 需要实现采购请求生成逻辑
"""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/{bom_id}/generate-pr", response_model=ResponseModel)
def generate_purchase_request_from_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    supplier_id: Optional[int] = Body(None),
    create_requests: bool = Body(True),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel:
    """从BOM生成采购需求/采购申请
    TODO: 实现采购请求生成逻辑
    """
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # TODO: 实现采购请求生成逻辑
    return ResponseModel(code=501, message="此功能正在开发中", data={"bom_id": bom_id})
