# -*- coding: utf-8 -*-
"""
外协订单 - 自动生成
从 outsourcing.py 拆分
"""

# -*- coding: utf-8 -*-
"""
外协管理 API endpoints
包含：外协供应商、外协订单、交付与质检、进度与付款
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.outsourcing import (
    OutsourcingOrder,
    OutsourcingOrderItem,
)
from app.models.vendor import Vendor
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.common.pagination import get_pagination_query, PaginationParams
from app.schemas.outsourcing import (
    OutsourcingOrderCreate,
    OutsourcingOrderItemResponse,
    OutsourcingOrderListResponse,
    OutsourcingOrderResponse,
    OutsourcingOrderUpdate,
)

router = APIRouter()

# 使用统一的编码生成工具
from app.utils.domain_codes import outsourcing as outsourcing_codes
from app.common.query_filters import apply_pagination

generate_order_no = outsourcing_codes.generate_order_no
generate_delivery_no = outsourcing_codes.generate_delivery_no
generate_inspection_no = outsourcing_codes.generate_inspection_no


# NOTE: keep flat routes (no extra prefix) to preserve the original API paths.
# 共 6 个路由

# ==================== 外协订单 ====================

@router.get("/outsourcing-orders", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_orders(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（订单号/标题）"),
    vendor_id: Optional[int] = Query(None, description="外协商ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    order_type: Optional[str] = Query(None, description="订单类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协订单列表
    """
    query = db.query(OutsourcingOrder)

    # 应用关键词过滤（订单号/标题）
    from app.common.query_filters import apply_keyword_filter
    query = apply_keyword_filter(query, OutsourcingOrder, keyword, ["order_no", "order_title"])

    if vendor_id:
        query = query.filter(OutsourcingOrder.vendor_id == vendor_id)

    if project_id:
        query = query.filter(OutsourcingOrder.project_id == project_id)

    if order_type:
        query = query.filter(OutsourcingOrder.order_type == order_type)

    if status:
        query = query.filter(OutsourcingOrder.status == status)

    total = query.count()
    orders = apply_pagination(query.order_by(desc(OutsourcingOrder.created_at)), pagination.offset, pagination.limit).all()

    items = []
    for order in orders:
        vendor = db.query(Vendor).filter(
            Vendor.id == order.vendor_id,
            Vendor.vendor_type == 'OUTSOURCING'
        ).first()
        project = db.query(Project).filter(Project.id == order.project_id).first()

        items.append(OutsourcingOrderListResponse(
            id=order.id,
            order_no=order.order_no,
            vendor_name=vendor.supplier_name if vendor else None,
            project_name=project.project_name if project else None,
            order_type=order.order_type,
            order_title=order.order_title,
            amount_with_tax=order.amount_with_tax or Decimal("0"),
            required_date=order.required_date,
            status=order.status,
            payment_status=order.payment_status,
            created_at=order.created_at
        ))

    return pagination.to_response(items, total)


@router.get("/outsourcing-orders/{order_id}", response_model=OutsourcingOrderResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协订单详情
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")

    vendor = db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
    project = db.query(Project).filter(Project.id == order.project_id).first()
    machine = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()

    # 获取订单明细
    items_data = []
    order_items = db.query(OutsourcingOrderItem).filter(OutsourcingOrderItem.order_id == order_id).order_by(OutsourcingOrderItem.item_no).all()
    for item in order_items:
        items_data.append(OutsourcingOrderItemResponse(
            id=item.id,
            item_no=item.item_no,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            drawing_no=item.drawing_no,
            process_type=item.process_type,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item.amount,
            material_provided=item.material_provided,
            delivered_quantity=item.delivered_quantity or Decimal("0"),
            qualified_quantity=item.qualified_quantity or Decimal("0"),
            rejected_quantity=item.rejected_quantity or Decimal("0"),
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))

    return OutsourcingOrderResponse(
        id=order.id,
        order_no=order.order_no,
        vendor_id=order.vendor_id,
        vendor_name=vendor.supplier_name if vendor else None,
        project_id=order.project_id,
        project_name=project.project_name if project else None,
        machine_id=order.machine_id,
        machine_name=machine.machine_name if machine else None,
        order_type=order.order_type,
        order_title=order.order_title,
        total_amount=order.total_amount or Decimal("0"),
        tax_rate=order.tax_rate or Decimal("13"),
        tax_amount=order.tax_amount or Decimal("0"),
        amount_with_tax=order.amount_with_tax or Decimal("0"),
        required_date=order.required_date,
        estimated_date=order.estimated_date,
        actual_date=order.actual_date,
        status=order.status,
        payment_status=order.payment_status,
        paid_amount=order.paid_amount or Decimal("0"),
        items=items_data,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.post("/outsourcing-orders", response_model=OutsourcingOrderResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: OutsourcingOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建外协订单
    """
    # 验证外协商
    vendor = db.query(Vendor).filter(
        Vendor.id == order_in.vendor_id,
        Vendor.vendor_type == 'OUTSOURCING'
    ).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")

    # 验证项目
    project = db.query(Project).filter(Project.id == order_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证机台（如果提供）
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine or machine.project_id != order_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")

    if not order_in.items:
        raise HTTPException(status_code=400, detail="订单明细不能为空")

    order_no = generate_order_no(db)

    # 计算金额
    total_amount = Decimal("0")
    for item in order_in.items:
        item_amount = item.quantity * item.unit_price
        total_amount += item_amount

    tax_amount = total_amount * (order_in.tax_rate / 100)
    amount_with_tax = total_amount + tax_amount

    order = OutsourcingOrder(
        order_no=order_no,
        vendor_id=order_in.vendor_id,
        project_id=order_in.project_id,
        machine_id=order_in.machine_id,
        order_type=order_in.order_type,
        order_title=order_in.order_title,
        order_description=order_in.order_description,
        tax_rate=order_in.tax_rate,
        total_amount=total_amount,
        tax_amount=tax_amount,
        amount_with_tax=amount_with_tax,
        required_date=order_in.required_date,
        contract_no=order_in.contract_no,
        status="DRAFT",
        created_by=current_user.id,
        remark=order_in.remark
    )

    db.add(order)
    db.flush()  # 获取order.id

    # 创建订单明细
    for idx, item_in in enumerate(order_in.items, start=1):
        item_amount = item_in.quantity * item_in.unit_price
        item = OutsourcingOrderItem(
            order_id=order.id,
            item_no=idx,
            material_id=item_in.material_id,
            material_code=item_in.material_code,
            material_name=item_in.material_name,
            specification=item_in.specification,
            drawing_no=item_in.drawing_no,
            process_type=item_in.process_type,
            process_content=item_in.process_content,
            process_requirements=item_in.process_requirements,
            unit=item_in.unit,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            amount=item_amount,
            material_provided=item_in.material_provided,
            provided_quantity=item_in.provided_quantity or Decimal("0"),
            remark=item_in.remark
        )
        db.add(item)

    db.commit()
    db.refresh(order)

    return read_outsourcing_order(order.id, db, current_user)


@router.put("/outsourcing-orders/{order_id}", response_model=OutsourcingOrderResponse, status_code=status.HTTP_200_OK)
def update_outsourcing_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    order_in: OutsourcingOrderUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新外协订单
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")

    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能修改草稿状态的订单")

    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_outsourcing_order(order_id, db, current_user)


@router.put("/outsourcing-orders/{order_id}/approve", response_model=OutsourcingOrderResponse, status_code=status.HTTP_200_OK)
def approve_outsourcing_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协订单审批
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")

    if order.status not in ["DRAFT", "SUBMITTED"]:
        raise HTTPException(status_code=400, detail="只能审批草稿或已提交状态的订单")

    order.status = "APPROVED"

    # 更新外协商的最后订单日期
    vendor = db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
    if vendor:
        vendor.last_order_date = datetime.now().date()
        db.add(vendor)

    db.add(order)
    db.commit()

    # 审批通过时自动归集成本
    if order.project_id:
        try:
            from app.services.cost_collection_service import CostCollectionService
            CostCollectionService.collect_from_outsourcing_order(
                db, order_id, created_by=current_user.id
            )
            db.commit()
        except Exception as e:
            # 成本归集失败不影响审批流程，只记录错误
            logger.error(f"Failed to collect cost from outsourcing order {order_id}: {e}")

    db.refresh(order)

    return read_outsourcing_order(order_id, db, current_user)


@router.get("/outsourcing-orders/{order_id}/items", response_model=List[OutsourcingOrderItemResponse], status_code=status.HTTP_200_OK)
def read_outsourcing_order_items(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协订单明细
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")

    items = db.query(OutsourcingOrderItem).filter(OutsourcingOrderItem.order_id == order_id).order_by(OutsourcingOrderItem.item_no).all()

    items_data = []
    for item in items:
        items_data.append(OutsourcingOrderItemResponse(
            id=item.id,
            item_no=item.item_no,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            drawing_no=item.drawing_no,
            process_type=item.process_type,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item.amount,
            material_provided=item.material_provided,
            delivered_quantity=item.delivered_quantity or Decimal("0"),
            qualified_quantity=item.qualified_quantity or Decimal("0"),
            rejected_quantity=item.rejected_quantity or Decimal("0"),
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))

    return items_data


