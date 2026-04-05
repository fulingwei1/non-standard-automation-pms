# -*- coding: utf-8 -*-
"""
BOM生成采购请求 - 从 bom.py 拆分
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.purchase.utils import generate_request_no
from app.core import security
from app.models.material import BomHeader
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.purchase_request_from_bom_service import (
    create_purchase_requests_from_bom,
    preview_purchase_requests_from_bom,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.post("/{bom_id}/generate-pr", response_model=ResponseModel)
def generate_purchase_request_from_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    supplier_id: Optional[int] = Query(None),
    create_requests: Optional[bool] = Query(None),
    payload: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel:
    """
    从BOM生成采购需求。

    兼容两种调用方式：
    - Query 参数：?supplier_id=1&create_requests=false （前端现状）
    - JSON Body：{"supplier_id": 1, "create_requests": true}（旧调用）
    """
    bom = get_or_404(db, BomHeader, bom_id, "BOM不存在")
    payload = payload or {}

    effective_supplier_id = supplier_id if supplier_id is not None else payload.get("supplier_id")
    effective_create_requests = (
        create_requests if create_requests is not None else payload.get("create_requests", True)
    )

    preview = preview_purchase_requests_from_bom(
        db=db,
        bom=bom,
        supplier_id=effective_supplier_id,
    )
    if not preview["purchase_requests"]:
        return ResponseModel(
            code=400,
            message="BOM中没有可生成的采购需求（可能已生成或已直接下单）",
            data={"bom_id": bom_id, "purchase_requests": [], "summary": preview["summary"]},
        )

    if not effective_create_requests:
        return ResponseModel(code=200, message="采购需求预览成功", data=preview)

    result = create_purchase_requests_from_bom(
        db=db,
        bom=bom,
        current_user_id=current_user.id,
        supplier_id=effective_supplier_id,
        generate_request_no=generate_request_no,
    )
    db.commit()
    return ResponseModel(code=200, message="采购需求生成成功", data=result)
