# -*- coding: utf-8 -*-
"""
外协交付 - 自动生成
从 outsourcing.py 拆分
"""

# -*- coding: utf-8 -*-
"""
外协管理 API endpoints
包含：外协供应商、外协订单、交付与质检、进度与付款
"""

import logging
from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.outsourcing import (
    OutsourcingVendor, OutsourcingOrder, OutsourcingOrderItem,
    OutsourcingDelivery, OutsourcingDeliveryItem,
    OutsourcingInspection, OutsourcingProgress, OutsourcingEvaluation, OutsourcingPayment
)
from app.schemas.outsourcing import (
    VendorCreate, VendorUpdate, VendorResponse,
    OutsourcingOrderCreate, OutsourcingOrderUpdate, OutsourcingOrderResponse, OutsourcingOrderListResponse,
    OutsourcingOrderItemCreate, OutsourcingOrderItemResponse,
    OutsourcingDeliveryCreate, OutsourcingDeliveryResponse,
    OutsourcingInspectionCreate, OutsourcingInspectionResponse,
    OutsourcingProgressCreate, OutsourcingProgressResponse,
    OutsourcingPaymentCreate, OutsourcingPaymentUpdate, OutsourcingPaymentResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_order_no(db: Session) -> str:
    """生成外协订单号：OS-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_order = (
        db.query(OutsourcingOrder)
        .filter(OutsourcingOrder.order_no.like(f"OS-{today}-%"))
        .order_by(desc(OutsourcingOrder.order_no))
        .first()
    )
    if max_order:
        seq = int(max_order.order_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"OS-{today}-{seq:03d}"


def generate_delivery_no(db: Session) -> str:
    """生成交付单号：DL-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_delivery = (
        db.query(OutsourcingDelivery)
        .filter(OutsourcingDelivery.delivery_no.like(f"DL-{today}-%"))
        .order_by(desc(OutsourcingDelivery.delivery_no))
        .first()
    )
    if max_delivery:
        seq = int(max_delivery.delivery_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"DL-{today}-{seq:03d}"


def generate_inspection_no(db: Session) -> str:
    """生成质检单号：IQ-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_inspection = (
        db.query(OutsourcingInspection)
        .filter(OutsourcingInspection.inspection_no.like(f"IQ-{today}-%"))
        .order_by(desc(OutsourcingInspection.inspection_no))
        .first()
    )
    if max_inspection:
        seq = int(max_inspection.inspection_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"IQ-{today}-{seq:03d}"



from fastapi import APIRouter

router = APIRouter(
    prefix="/outsourcing/deliveries",
    tags=["deliveries"]
)

# 共 2 个路由

# ==================== 外协交付 ====================

@router.get("/outsourcing-deliveries", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_deliveries(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    order_id: Optional[int] = Query(None, description="订单ID筛选"),
    vendor_id: Optional[int] = Query(None, description="外协商ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取交付记录列表
    """
    query = db.query(OutsourcingDelivery)
    
    if order_id:
        query = query.filter(OutsourcingDelivery.order_id == order_id)
    
    if vendor_id:
        query = query.filter(OutsourcingDelivery.vendor_id == vendor_id)
    
    if status:
        query = query.filter(OutsourcingDelivery.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    deliveries = query.order_by(desc(OutsourcingDelivery.delivery_date)).offset(offset).limit(page_size).all()
    
    items = []
    for delivery in deliveries:
        vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == delivery.vendor_id).first()
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery.order_id).first()
        
        items.append(OutsourcingDeliveryResponse(
            id=delivery.id,
            delivery_no=delivery.delivery_no,
            order_id=delivery.order_id,
            order_no=order.order_no if order else None,
            vendor_name=vendor.vendor_name if vendor else None,
            delivery_date=delivery.delivery_date,
            delivery_type=delivery.delivery_type,
            status=delivery.status,
            received_at=delivery.received_at,
            created_at=delivery.created_at,
            updated_at=delivery.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/outsourcing-deliveries", response_model=OutsourcingDeliveryResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_delivery(
    *,
    db: Session = Depends(deps.get_db),
    delivery_in: OutsourcingDeliveryCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建交付记录
    """
    # 验证订单
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery_in.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    if order.status not in ["APPROVED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="只能为已审批或进行中的订单创建交付记录")
    
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == order.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")
    
    if not delivery_in.items:
        raise HTTPException(status_code=400, detail="交付明细不能为空")
    
    delivery_no = generate_delivery_no(db)
    
    delivery = OutsourcingDelivery(
        delivery_no=delivery_no,
        order_id=delivery_in.order_id,
        vendor_id=order.vendor_id,
        delivery_date=delivery_in.delivery_date,
        delivery_type=delivery_in.delivery_type,
        delivery_person=delivery_in.delivery_person,
        logistics_company=delivery_in.logistics_company,
        tracking_no=delivery_in.tracking_no,
        status="PENDING",
        created_by=current_user.id,
        remark=delivery_in.remark
    )
    
    db.add(delivery)
    db.flush()  # 获取delivery.id
    
    # 创建交付明细
    for item_in in delivery_in.items:
        order_item = db.query(OutsourcingOrderItem).filter(OutsourcingOrderItem.id == item_in.order_item_id).first()
        if not order_item or order_item.order_id != delivery_in.order_id:
            raise HTTPException(status_code=400, detail=f"订单明细ID {item_in.order_item_id} 不存在或不属于该订单")
        
        delivery_item = OutsourcingDeliveryItem(
            delivery_id=delivery.id,
            order_item_id=item_in.order_item_id,
            material_code=order_item.material_code,
            material_name=order_item.material_name,
            delivery_quantity=item_in.delivery_quantity,
            remark=item_in.remark
        )
        db.add(delivery_item)
        
        # 更新订单明细的已交付数量
        order_item.delivered_quantity = (order_item.delivered_quantity or Decimal("0")) + item_in.delivery_quantity
        db.add(order_item)
    
    # 更新订单状态
    if order.status == "APPROVED":
        order.status = "IN_PROGRESS"
        db.add(order)
    
    db.commit()
    db.refresh(delivery)
    
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == delivery.vendor_id).first()
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery.order_id).first()
    
    return OutsourcingDeliveryResponse(
        id=delivery.id,
        delivery_no=delivery.delivery_no,
        order_id=delivery.order_id,
        order_no=order.order_no if order else None,
        vendor_name=vendor.vendor_name if vendor else None,
        delivery_date=delivery.delivery_date,
        delivery_type=delivery.delivery_type,
        status=delivery.status,
        received_at=delivery.received_at,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at
    )



