# -*- coding: utf-8 -*-
"""
采购申请端点（重构版）
使用统一响应格式
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.core.schemas import paginated_response, success_response
from app.models.purchase import (
    PurchaseRequest,
    PurchaseRequestItem,
)
from app.models.user import User

from app.common.pagination import PaginationParams, get_pagination_query
from .utils import (
    decimal_value,
    generate_request_no,
    serialize_purchase_request,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/requests")
def list_purchase_requests(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="按状态筛选: DRAFT, SUBMITTED, APPROVED, REJECTED"),
    current_user: User = Depends(get_current_active_user),
):
    """获取采购申请列表"""
    query = db.query(PurchaseRequest)
    if status:
        query = query.filter(PurchaseRequest.status == status)
    total = query.count()
    requests = apply_pagination(query.order_by(desc(PurchaseRequest.created_at)), pagination.offset, pagination.limit).all()
    
    items = [serialize_purchase_request(r, include_items=False) for r in requests]
    pages = pagination.pages_for_total(total)
    
    # 使用统一响应格式
    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
        message="获取采购申请列表成功"
    )


@router.post("/requests")
def create_purchase_request(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建采购申请"""
    items_payload = payload.get("items") or []
    if not items_payload:
        raise HTTPException(status_code=400, detail="采购申请至少需要 1 条明细")

    required_date = payload.get("required_date")
    parsed_required_date: Optional[date] = None
    if required_date:
        parsed_required_date = date.fromisoformat(required_date)

    request = PurchaseRequest(
        request_no=generate_request_no(db),
        project_id=payload.get("project_id"),
        machine_id=payload.get("machine_id"),
        supplier_id=payload.get("supplier_id"),
        request_type=payload.get("request_type") or "NORMAL",
        request_reason=payload.get("request_reason"),
        required_date=parsed_required_date,
        status="DRAFT",
        requested_by=current_user.id,
        requested_at=datetime.now(),
        created_by=current_user.id,
    )
    db.add(request)
    db.flush()

    total_amount = Decimal("0")
    for item in items_payload:
        qty = decimal_value(item.get("quantity"), "0")
        unit_price = decimal_value(item.get("unit_price"), "0")
        amount = qty * unit_price
        total_amount += amount
        request_item = PurchaseRequestItem(
            request_id=request.id,
            material_id=item.get("material_id"),
            material_code=item.get("material_code") or "",
            material_name=item.get("material_name") or "",
            specification=item.get("specification"),
            unit=item.get("unit") or "件",
            quantity=qty,
            unit_price=unit_price,
            amount=amount,
            required_date=parsed_required_date,
        )
        db.add(request_item)

    request.total_amount = total_amount
    db.commit()
    db.refresh(request)
    
    # 使用统一响应格式
    return success_response(
        data=serialize_purchase_request(request, include_items=True),
        message="采购申请创建成功"
    )


@router.get("/requests/{request_id}")
def get_purchase_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取采购申请详情"""
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    
    # 使用统一响应格式
    return success_response(
        data=serialize_purchase_request(request, include_items=True),
        message="获取采购申请详情成功"
    )


@router.put("/requests/{request_id}/submit")
def submit_purchase_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """提交采购申请"""
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if request.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态可提交")
    if request.items.count() == 0:
        raise HTTPException(status_code=400, detail="采购申请没有明细")
    request.status = "SUBMITTED"
    request.submitted_at = datetime.now()
    db.commit()
    
    # 使用统一响应格式
    return success_response(
        data=None,
        message="采购申请提交成功"
    )


@router.put("/requests/{request_id}/approve")
def approve_purchase_request(
    request_id: int,
    approved: bool = Query(True),
    approval_note: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """审批采购申请"""
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if request.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只有已提交的申请可审批")
    request.approved_by = current_user.id
    request.approved_at = datetime.now()
    request.approval_note = approval_note
    request.status = "APPROVED" if approved else "REJECTED"
    db.commit()
    
    # 使用统一响应格式
    return success_response(
        data=None,
        message="采购申请审批完成"
    )


@router.delete("/requests/{request_id}")
def delete_purchase_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除采购申请"""
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if request.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态可删除")
    db.delete(request)
    db.commit()
    
    # 使用统一响应格式
    return success_response(
        data=None,
        message="采购申请已删除"
    )


@router.post("/requests/{request_id}/generate-orders")
def generate_orders_from_request(
    request_id: int,
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """从采购申请生成订单"""
    try:
        from app.services.purchase.purchase_service import PurchaseService
        service = PurchaseService(db)
        success = service.generate_orders_from_request(request_id, supplier_id)

        if success:
            # 使用统一响应格式
            return success_response(
                data=None,
                message="从采购申请生成订单成功"
            )
        else:
            raise HTTPException(status_code=404, detail="采购申请不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从采购申请生成订单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"从采购申请生成订单失败: {str(e)}")
