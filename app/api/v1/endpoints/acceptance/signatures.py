# -*- coding: utf-8 -*-
"""
验收报告 - 签字管理

包含验收签字的列表和创建
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceOrder, AcceptanceSignature
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceSignatureCreate,
    AcceptanceSignatureResponse,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/acceptance-orders/{order_id}/signatures", response_model=List[AcceptanceSignatureResponse], status_code=status.HTTP_200_OK)
def read_acceptance_signatures(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收签字列表
    """
    order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

    signatures = db.query(AcceptanceSignature).filter(AcceptanceSignature.order_id == order_id).order_by(AcceptanceSignature.signed_at).all()

    items = []
    for sig in signatures:
        items.append(AcceptanceSignatureResponse(
            id=sig.id,
            order_id=sig.order_id,
            signer_type=sig.signer_type,
            signer_role=sig.signer_role,
            signer_name=sig.signer_name,
            signer_company=sig.signer_company,
            signed_at=sig.signed_at,
            ip_address=sig.ip_address,
            created_at=sig.created_at,
            updated_at=sig.updated_at
        ))

    return items


@router.post("/acceptance-orders/{order_id}/signatures", response_model=AcceptanceSignatureResponse, status_code=status.HTTP_201_CREATED)
def add_acceptance_signature(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    order_id: int,
    signature_in: AcceptanceSignatureCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加签字
    """
    from datetime import datetime

    order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只能为已完成状态的验收单添加签字")

    if signature_in.order_id != order_id:
        raise HTTPException(status_code=400, detail="签字所属验收单ID不匹配")

    signature = AcceptanceSignature(
        order_id=order_id,
        signer_type=signature_in.signer_type,
        signer_role=signature_in.signer_role,
        signer_name=signature_in.signer_name,
        signer_company=signature_in.signer_company,
        signature_data=signature_in.signature_data,
        signed_at=datetime.now(),
        ip_address=request.client.host if request and request.client else None
    )

    # 如果是QA签字，更新验收单
    if signature_in.signer_type == "QA":
        order.qa_signer_id = current_user.id
        order.qa_signed_at = datetime.now()
        db.add(order)

    # 如果是客户签字，更新验收单
    if signature_in.signer_type == "CUSTOMER":
        order.customer_signer = signature_in.signer_name
        order.customer_signed_at = datetime.now()
        order.customer_signature = signature_in.signature_data
        db.add(order)

    db.add(signature)
    db.commit()
    db.refresh(signature)

    return AcceptanceSignatureResponse(
        id=signature.id,
        order_id=signature.order_id,
        signer_type=signature.signer_type,
        signer_role=signature.signer_role,
        signer_name=signature.signer_name,
        signer_company=signature.signer_company,
        signed_at=signature.signed_at,
        ip_address=signature.ip_address,
        created_at=signature.created_at,
        updated_at=signature.updated_at
    )
