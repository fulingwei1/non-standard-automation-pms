# -*- coding: utf-8 -*-
"""
BOM生成采购请求 - 从 bom.py 拆分
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_like_filter
from app.core import security
from app.models.material import BomHeader, BomItem
from app.models.purchase import PurchaseRequest, PurchaseRequestItem
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


def generate_pr_no(db: Session) -> str:
    """生成采购申请单号：PR-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"PR-{today}-"

    # 查询当天最大编号
    last_request_query = db.query(PurchaseRequest)
    last_request_query = apply_like_filter(
        last_request_query,
        PurchaseRequest,
        f"{prefix}%",
        "request_no",
        use_ilike=False,
    )
    last_request = last_request_query.order_by(PurchaseRequest.request_no.desc()).first()

    if last_request:
        last_no = int(last_request.request_no.split("-")[-1])
        new_no = last_no + 1
    else:
        new_no = 1

    return f"{prefix}{new_no:03d}"


@router.post("/{bom_id}/generate-pr", response_model=ResponseModel)
def generate_purchase_request_from_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    supplier_id: Optional[int] = Body(None),
    create_requests: bool = Body(True),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel:
    """从BOM生成采购需求/采购申请"""
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 获取BOM明细
    bom_items = db.query(BomItem).filter(
        BomItem.bom_id == bom_id,
        BomItem.source_type.in_(['PURCHASE', 'OUTSOURCE'])  # 只选择需要采购/外协的物料
    ).all()

    if not bom_items:
        return ResponseModel(
            code=400,
            message="BOM中没有需要采购的物料",
            data={"bom_id": bom_id}
        )

    # 创建采购申请单
    pr = PurchaseRequest(
        request_no=generate_pr_no(db),
        project_id=bom.project_id,
        machine_id=bom.machine_id,
        supplier_id=supplier_id,
        source_type='BOM',
        source_id=bom_id,
        request_reason=f"从BOM {bom.bom_no} 生成",
        status='DRAFT',
        requested_by=current_user.id,
        created_by=current_user.id
    )
    db.add(pr)
    db.flush()

    # 创建采购申请明细
    total_amount = Decimal('0')
    for item in bom_items:
        unit_price = item.unit_price or Decimal('0')
        quantity = item.quantity or Decimal('0')
        amount = unit_price * quantity

        pr_item = PurchaseRequestItem(
            request_id=pr.id,
            bom_item_id=item.id,
            material_id=item.material_id,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            unit=item.unit,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount
        )
        db.add(pr_item)
        total_amount += amount

    # 更新总金额
    pr.total_amount = total_amount

    db.commit()
    db.refresh(pr)

    return ResponseModel(
        code=200,
        message="采购申请生成成功",
        data={
            "request_id": pr.id,
            "request_no": pr.request_no,
            "item_count": len(bom_items),
            "total_amount": float(total_amount)
        }
    )
