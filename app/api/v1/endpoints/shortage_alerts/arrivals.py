# -*- coding: utf-8 -*-
"""
到货跟踪 - 自动生成
从 shortage_alerts.py 拆分
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import BomItem, Material, MaterialShortage
from app.models.production import WorkOrder
from app.models.project import Machine, Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.shortage import (
    ArrivalFollowUp,
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageReport,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.shortage import (
    ArrivalFollowUpCreate,
    MaterialArrivalListResponse,
    MaterialArrivalResponse,
    MaterialSubstitutionCreate,
    MaterialSubstitutionListResponse,
    MaterialSubstitutionResponse,
    MaterialTransferCreate,
    MaterialTransferListResponse,
    MaterialTransferResponse,
    ShortageReportCreate,
    ShortageReportListResponse,
    ShortageReportResponse,
)

from .utils import generate_arrival_no

router = APIRouter(tags=["arrivals"])

# 共 6 个路由

@router.get("/arrivals", response_model=PaginatedResponse, status_code=200)
def read_material_arrivals(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    shortage_report_id: Optional[int] = Query(None, description="缺料上报ID筛选"),
    purchase_order_id: Optional[int] = Query(None, description="采购订单ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    is_delayed: Optional[bool] = Query(None, description="是否延迟筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    到货跟踪列表
    """
    query = db.query(MaterialArrival)

    if shortage_report_id:
        query = query.filter(MaterialArrival.shortage_report_id == shortage_report_id)
    if purchase_order_id:
        query = query.filter(MaterialArrival.purchase_order_id == purchase_order_id)
    if status:
        query = query.filter(MaterialArrival.status == status)
    if is_delayed is not None:
        query = query.filter(MaterialArrival.is_delayed == is_delayed)

    total = query.count()
    offset = (page - 1) * page_size
    arrivals = query.order_by(MaterialArrival.expected_date).offset(offset).limit(page_size).all()

    items = []
    for arrival in arrivals:
        from app.models.material import Supplier
        supplier = None
        if arrival.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == arrival.supplier_id).first()

        items.append(MaterialArrivalResponse(
            id=arrival.id,
            arrival_no=arrival.arrival_no,
            shortage_report_id=arrival.shortage_report_id,
            purchase_order_id=arrival.purchase_order_id,
            material_id=arrival.material_id,
            material_code=arrival.material_code,
            material_name=arrival.material_name,
            expected_qty=arrival.expected_qty,
            supplier_id=arrival.supplier_id,
            supplier_name=supplier.supplier_name if supplier else arrival.supplier_name,
            expected_date=arrival.expected_date,
            actual_date=arrival.actual_date,
            is_delayed=arrival.is_delayed,
            delay_days=arrival.delay_days,
            status=arrival.status,
            received_qty=arrival.received_qty or Decimal("0"),
            received_by=arrival.received_by,
            received_at=arrival.received_at,
            follow_up_count=arrival.follow_up_count,
            remark=arrival.remark,
            created_at=arrival.created_at,
            updated_at=arrival.updated_at
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/arrivals", response_model=MaterialArrivalResponse, status_code=201)
def create_material_arrival(
    *,
    db: Session = Depends(deps.get_db),
    shortage_report_id: Optional[int] = Query(None, description="缺料上报ID"),
    purchase_order_item_id: Optional[int] = Query(None, description="采购订单明细ID"),
    material_id: int = Query(..., description="物料ID"),
    expected_qty: Decimal = Query(..., gt=0, description="预期到货数量"),
    expected_date: date = Query(..., description="预期到货日期"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    current_user: User = Depends(security.require_permission("shortage_alert:create")),
) -> Any:
    """
    创建交付记录（从采购订单或缺料上报创建）
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    purchase_order_id = None
    if purchase_order_item_id:
        po_item = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == purchase_order_item_id).first()
        if not po_item:
            raise HTTPException(status_code=404, detail="采购订单明细不存在")
        purchase_order_id = po_item.order_id

    if shortage_report_id:
        report = db.query(ShortageReport).filter(ShortageReport.id == shortage_report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="缺料上报不存在")

    from app.models.material import Supplier
    supplier_name = None
    if supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        supplier_name = supplier.supplier_name if supplier else None

    arrival_no = generate_arrival_no(db)

    arrival = MaterialArrival(
        arrival_no=arrival_no,
        shortage_report_id=shortage_report_id,
        purchase_order_id=purchase_order_id,
        purchase_order_item_id=purchase_order_item_id,
        material_id=material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        expected_qty=expected_qty,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        expected_date=expected_date,
        status="PENDING"
    )

    db.add(arrival)
    db.commit()
    db.refresh(arrival)

    return read_material_arrival(arrival.id, db, current_user)


@router.get("/arrivals/{arrival_id}", response_model=MaterialArrivalResponse, status_code=200)
def read_material_arrival(
    arrival_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    到货跟踪详情
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    from app.models.material import Supplier
    supplier = None
    if arrival.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == arrival.supplier_id).first()

    return MaterialArrivalResponse(
        id=arrival.id,
        arrival_no=arrival.arrival_no,
        shortage_report_id=arrival.shortage_report_id,
        purchase_order_id=arrival.purchase_order_id,
        material_id=arrival.material_id,
        material_code=arrival.material_code,
        material_name=arrival.material_name,
        expected_qty=arrival.expected_qty,
        supplier_id=arrival.supplier_id,
        supplier_name=supplier.supplier_name if supplier else arrival.supplier_name,
        expected_date=arrival.expected_date,
        actual_date=arrival.actual_date,
        is_delayed=arrival.is_delayed,
        delay_days=arrival.delay_days,
        status=arrival.status,
        received_qty=arrival.received_qty or Decimal("0"),
        received_by=arrival.received_by,
        received_at=arrival.received_at,
        follow_up_count=arrival.follow_up_count,
        remark=arrival.remark,
        created_at=arrival.created_at,
        updated_at=arrival.updated_at
    )


@router.put("/arrivals/{arrival_id}/status", response_model=MaterialArrivalResponse, status_code=200)
def update_arrival_status(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    status: str = Query(..., description="状态：PENDING/IN_TRANSIT/DELAYED/RECEIVED/CANCELLED"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    更新到货状态
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    arrival.status = status

    # 如果标记为延迟，计算延迟天数
    if status == "DELAYED" and arrival.expected_date:
        today = datetime.now().date()
        if today > arrival.expected_date:
            arrival.is_delayed = True
            arrival.delay_days = (today - arrival.expected_date).days

    db.add(arrival)
    db.commit()
    db.refresh(arrival)

    return read_material_arrival(arrival_id, db, current_user)


@router.post("/arrivals/{arrival_id}/follow-up", response_model=ResponseModel, status_code=201)
def create_arrival_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    follow_up_in: ArrivalFollowUpCreate,
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    创建跟催记录
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    follow_up = ArrivalFollowUp(
        arrival_id=arrival_id,
        follow_up_type=follow_up_in.follow_up_type,
        follow_up_note=follow_up_in.follow_up_note,
        supplier_response=follow_up_in.supplier_response,
        next_follow_up_date=follow_up_in.next_follow_up_date,
        followed_by=current_user.id
    )

    arrival.follow_up_count = (arrival.follow_up_count or 0) + 1
    arrival.last_follow_up_at = datetime.now()

    db.add(follow_up)
    db.add(arrival)
    db.commit()

    return ResponseModel(message="跟催记录创建成功")


@router.post("/arrivals/{arrival_id}/receive", response_model=MaterialArrivalResponse, status_code=200)
def receive_material_arrival(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    received_qty: Decimal = Query(..., gt=0, description="实收数量"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    确认收货
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    if arrival.status == "RECEIVED":
        raise HTTPException(status_code=400, detail="已经收货")

    arrival.status = "RECEIVED"
    arrival.received_qty = received_qty
    arrival.received_by = current_user.id
    arrival.received_at = datetime.now()
    arrival.actual_date = datetime.now().date()

    # 更新延迟状态
    if arrival.expected_date and arrival.actual_date > arrival.expected_date:
        arrival.is_delayed = True
        arrival.delay_days = (arrival.actual_date - arrival.expected_date).days

    db.add(arrival)
    db.commit()
    db.refresh(arrival)

    return read_material_arrival(arrival_id, db, current_user)

