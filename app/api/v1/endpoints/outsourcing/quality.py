# -*- coding: utf-8 -*-
"""
外协质检 - 自动生成
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
from app.common.pagination import PaginationParams, get_pagination_query
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
# 共 3 个路由

# ==================== 外协质检 ====================

@router.get("/outsourcing-inspections", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_inspections(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    delivery_id: Optional[int] = Query(None, description="交付单ID筛选"),
    inspect_result: Optional[str] = Query(None, description="质检结果筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取质检记录列表
    """
    query = db.query(OutsourcingInspection)

    if delivery_id:
        query = query.filter(OutsourcingInspection.delivery_id == delivery_id)

    if inspect_result:
        query = query.filter(OutsourcingInspection.inspect_result == inspect_result)

    total = query.count()
    inspections = apply_pagination(query.order_by(desc(OutsourcingInspection.inspect_date)), pagination.offset, pagination.limit).all()

    items = []
    for inspection in inspections:
        pass_rate = Decimal("0")
        if inspection.inspect_quantity and inspection.inspect_quantity > 0:
            pass_rate = (inspection.qualified_quantity or Decimal("0")) / inspection.inspect_quantity * 100

        items.append(OutsourcingInspectionResponse(
            id=inspection.id,
            inspection_no=inspection.inspection_no,
            delivery_id=inspection.delivery_id,
            inspect_type=inspection.inspect_type,
            inspect_date=inspection.inspect_date,
            inspector_name=inspection.inspector_name,
            inspect_quantity=inspection.inspect_quantity,
            qualified_quantity=inspection.qualified_quantity or Decimal("0"),
            rejected_quantity=inspection.rejected_quantity or Decimal("0"),
            inspect_result=inspection.inspect_result,
            pass_rate=pass_rate,
            disposition=inspection.disposition,
            created_at=inspection.created_at,
            updated_at=inspection.updated_at
        ))

    return pagination.to_response(items, total)


@router.post("/outsourcing-inspections", response_model=OutsourcingInspectionResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_inspection(
    *,
    db: Session = Depends(deps.get_db),
    inspection_in: OutsourcingInspectionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建质检记录
    """
    # 验证交付明细
    delivery_item = db.query(OutsourcingDeliveryItem).filter(OutsourcingDeliveryItem.id == inspection_in.delivery_item_id).first()
    if not delivery_item:
        raise HTTPException(status_code=404, detail="交付明细不存在")

    if delivery_item.delivery_id != inspection_in.delivery_id:
        raise HTTPException(status_code=400, detail="交付明细不属于该交付单")

    if inspection_in.inspect_quantity > delivery_item.delivery_quantity:
        raise HTTPException(status_code=400, detail="送检数量不能大于交付数量")

    if inspection_in.qualified_quantity + inspection_in.rejected_quantity > inspection_in.inspect_quantity:
        raise HTTPException(status_code=400, detail="合格数量+不合格数量不能大于送检数量")

    inspection_no = generate_inspection_no(db)

    # 计算合格率
    pass_rate = Decimal("0")
    if inspection_in.inspect_quantity > 0:
        pass_rate = inspection_in.qualified_quantity / inspection_in.inspect_quantity * 100

    inspection = OutsourcingInspection(
        inspection_no=inspection_no,
        delivery_id=inspection_in.delivery_id,
        delivery_item_id=inspection_in.delivery_item_id,
        inspect_type=inspection_in.inspect_type,
        inspect_date=inspection_in.inspect_date,
        inspector_id=current_user.id,
        inspector_name=current_user.real_name or current_user.username,
        inspect_quantity=inspection_in.inspect_quantity,
        sample_quantity=inspection_in.sample_quantity or Decimal("0"),
        qualified_quantity=inspection_in.qualified_quantity,
        rejected_quantity=inspection_in.rejected_quantity,
        inspect_result=inspection_in.inspect_result,
        pass_rate=pass_rate,
        defect_description=inspection_in.defect_description,
        defect_type=inspection_in.defect_type,
        disposition=inspection_in.disposition,
        disposition_note=inspection_in.disposition_note,
        remark=inspection_in.remark
    )

    # 更新交付明细的质检结果
    delivery_item.inspect_status = "COMPLETED"
    delivery_item.qualified_quantity = inspection_in.qualified_quantity
    delivery_item.rejected_quantity = inspection_in.rejected_quantity

    # 更新订单明细的合格数量和不合格数量
    order_item = db.query(OutsourcingOrderItem).filter(OutsourcingOrderItem.id == delivery_item.order_item_id).first()
    if order_item:
        order_item.qualified_quantity = (order_item.qualified_quantity or Decimal("0")) + inspection_in.qualified_quantity
        order_item.rejected_quantity = (order_item.rejected_quantity or Decimal("0")) + inspection_in.rejected_quantity
        db.add(order_item)

    db.add(inspection)
    db.add(delivery_item)
    db.commit()
    db.refresh(inspection)

    pass_rate = Decimal("0")
    if inspection.inspect_quantity and inspection.inspect_quantity > 0:
        pass_rate = (inspection.qualified_quantity or Decimal("0")) / inspection.inspect_quantity * 100

    return OutsourcingInspectionResponse(
        id=inspection.id,
        inspection_no=inspection.inspection_no,
        delivery_id=inspection.delivery_id,
        inspect_type=inspection.inspect_type,
        inspect_date=inspection.inspect_date,
        inspector_name=inspection.inspector_name,
        inspect_quantity=inspection.inspect_quantity,
        qualified_quantity=inspection.qualified_quantity or Decimal("0"),
        rejected_quantity=inspection.rejected_quantity or Decimal("0"),
        inspect_result=inspection.inspect_result,
        pass_rate=pass_rate,
        disposition=inspection.disposition,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at
    )


@router.put("/outsourcing-inspections/{inspection_id}", response_model=OutsourcingInspectionResponse, status_code=status.HTTP_200_OK)
def update_outsourcing_inspection(
    *,
    db: Session = Depends(deps.get_db),
    inspection_id: int,
    inspect_result: Optional[str] = Query(None, description="质检结果"),
    disposition: Optional[str] = Query(None, description="处置方式"),
    disposition_note: Optional[str] = Query(None, description="处理说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新质检结果
    """
    inspection = db.query(OutsourcingInspection).filter(OutsourcingInspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="质检记录不存在")

    if inspect_result:
        inspection.inspect_result = inspect_result

    if disposition:
        inspection.disposition = disposition

    if disposition_note:
        inspection.disposition_note = disposition_note

    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    pass_rate = Decimal("0")
    if inspection.inspect_quantity and inspection.inspect_quantity > 0:
        pass_rate = (inspection.qualified_quantity or Decimal("0")) / inspection.inspect_quantity * 100

    return OutsourcingInspectionResponse(
        id=inspection.id,
        inspection_no=inspection.inspection_no,
        delivery_id=inspection.delivery_id,
        inspect_type=inspection.inspect_type,
        inspect_date=inspection.inspect_date,
        inspector_name=inspection.inspector_name,
        inspect_quantity=inspection.inspect_quantity,
        qualified_quantity=inspection.qualified_quantity or Decimal("0"),
        rejected_quantity=inspection.rejected_quantity or Decimal("0"),
        inspect_result=inspection.inspect_result,
        pass_rate=pass_rate,
        disposition=inspection.disposition,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at
    )


