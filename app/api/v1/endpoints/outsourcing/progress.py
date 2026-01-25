# -*- coding: utf-8 -*-
"""
外协进度 - 自动生成
从 outsourcing.py 拆分
"""

# -*- coding: utf-8 -*-
"""
外协管理 API endpoints
包含：外协供应商、外协订单、交付与质检、进度与付款
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.outsourcing import (
    OutsourcingDelivery,
    OutsourcingDeliveryItem,
    OutsourcingEvaluation,
    OutsourcingInspection,
    OutsourcingOrder,
    OutsourcingOrderItem,
    OutsourcingPayment,
    OutsourcingProgress,
)
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.outsourcing import (
    OutsourcingDeliveryCreate,
    OutsourcingDeliveryResponse,
    OutsourcingInspectionCreate,
    OutsourcingInspectionResponse,
    OutsourcingOrderCreate,
    OutsourcingOrderItemCreate,
    OutsourcingOrderItemResponse,
    OutsourcingOrderListResponse,
    OutsourcingOrderResponse,
    OutsourcingOrderUpdate,
    OutsourcingPaymentCreate,
    OutsourcingPaymentResponse,
    OutsourcingPaymentUpdate,
    OutsourcingProgressCreate,
    OutsourcingProgressResponse,
    VendorCreate,
    VendorResponse,
    VendorUpdate,
)

router = APIRouter()

# 使用统一的编码生成工具
from app.utils.domain_codes import outsourcing as outsourcing_codes

generate_order_no = outsourcing_codes.generate_order_no
generate_delivery_no = outsourcing_codes.generate_delivery_no
generate_inspection_no = outsourcing_codes.generate_inspection_no


# NOTE: keep flat routes (no extra prefix) to preserve the original API paths.
# 共 2 个路由

# ==================== 外协进度 ====================

@router.get("/outsourcing-orders/{order_id}/progress-logs", response_model=List[OutsourcingProgressResponse], status_code=status.HTTP_200_OK)
def read_outsourcing_progress_logs(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协进度列表
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")

    progress_records = db.query(OutsourcingProgress).filter(OutsourcingProgress.order_id == order_id).order_by(desc(OutsourcingProgress.report_date)).all()

    items = []
    for progress in progress_records:
        items.append(OutsourcingProgressResponse(
            id=progress.id,
            order_id=progress.order_id,
            report_date=progress.report_date,
            progress_pct=progress.progress_pct or 0,
            completed_quantity=progress.completed_quantity or Decimal("0"),
            current_process=progress.current_process,
            estimated_complete=progress.estimated_complete,
            issues=progress.issues,
            risk_level=progress.risk_level,
            created_at=progress.created_at,
            updated_at=progress.updated_at
        ))

    return items


@router.put("/outsourcing-orders/{order_id}/progress", response_model=OutsourcingProgressResponse, status_code=status.HTTP_200_OK)
def update_outsourcing_progress(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    progress_in: OutsourcingProgressCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协进度更新
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")

    if order.status not in ["APPROVED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="只能更新已审批或进行中订单的进度")

    progress = OutsourcingProgress(
        order_id=order_id,
        order_item_id=progress_in.order_item_id,
        report_date=progress_in.report_date,
        progress_pct=progress_in.progress_pct,
        completed_quantity=progress_in.completed_quantity or Decimal("0"),
        current_process=progress_in.current_process,
        next_process=progress_in.next_process,
        estimated_complete=progress_in.estimated_complete,
        issues=progress_in.issues,
        risk_level=progress_in.risk_level,
        attachments=progress_in.attachments,
        reported_by=current_user.id
    )

    db.add(progress)
    db.commit()
    db.refresh(progress)

    return OutsourcingProgressResponse(
        id=progress.id,
        order_id=progress.order_id,
        report_date=progress.report_date,
        progress_pct=progress.progress_pct or 0,
        completed_quantity=progress.completed_quantity or Decimal("0"),
        current_process=progress.current_process,
        estimated_complete=progress.estimated_complete,
        issues=progress.issues,
        risk_level=progress.risk_level,
        created_at=progress.created_at,
        updated_at=progress.updated_at
    )


