# -*- coding: utf-8 -*-
"""
到货跟踪 - 基础CRUD操作

包含创建、列表、详情、状态更新、收货、延迟查询
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import Material
from app.models.purchase import PurchaseOrder
from app.models.shortage import MaterialArrival, ShortageReport
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.shortage import (
    MaterialArrivalCreate,
    MaterialArrivalResponse,
)

from app.services.data_scope_service import DataScopeConfig

from .arrival_helpers import generate_arrival_no

router = APIRouter()

# 到货跟踪数据权限配置（无直接项目字段，仅按创建人过滤）
ARRIVAL_DATA_SCOPE_CONFIG = DataScopeConfig(
    owner_field=None,  # MaterialArrival 没有 created_by 字段
    project_field=None,  # 无直接项目关联
)


@router.post("/shortage/arrivals", response_model=MaterialArrivalResponse, status_code=status.HTTP_201_CREATED)
def create_arrival(
    *,
    db: Session = Depends(deps.get_db),
    arrival_in: MaterialArrivalCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建到货跟踪（从采购订单或缺料上报创建）
    """
    # 验证物料
    material = db.query(Material).filter(Material.id == arrival_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 如果关联缺料上报，验证上报存在
    if arrival_in.shortage_report_id:
        report = db.query(ShortageReport).filter(ShortageReport.id == arrival_in.shortage_report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="缺料上报不存在")

    # 如果关联采购订单，验证订单存在
    if arrival_in.purchase_order_id:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == arrival_in.purchase_order_id).first()
        if not po:
            raise HTTPException(status_code=404, detail="采购订单不存在")

    # 如果提供了供应商ID，验证供应商存在
    supplier = None
    if arrival_in.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == arrival_in.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")

    arrival = MaterialArrival(
        arrival_no=generate_arrival_no(db),
        shortage_report_id=arrival_in.shortage_report_id,
        purchase_order_id=arrival_in.purchase_order_id,
        purchase_order_item_id=arrival_in.purchase_order_item_id,
        material_id=arrival_in.material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        expected_qty=arrival_in.expected_qty,
        supplier_id=arrival_in.supplier_id,
        supplier_name=arrival_in.supplier_name or (supplier.supplier_name if supplier else None),
        expected_date=arrival_in.expected_date,
        status='PENDING',
        remark=arrival_in.remark
    )

    db.add(arrival)
    db.commit()
    db.refresh(arrival)

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
        supplier_name=arrival.supplier_name,
        expected_date=arrival.expected_date,
        actual_date=arrival.actual_date,
        is_delayed=arrival.is_delayed,
        delay_days=arrival.delay_days,
        status=arrival.status,
        received_qty=arrival.received_qty,
        received_by=arrival.received_by,
        received_at=arrival.received_at,
        follow_up_count=arrival.follow_up_count,
        remark=arrival.remark,
        created_at=arrival.created_at,
        updated_at=arrival.updated_at,
    )


@router.get("/shortage/arrivals", response_model=PaginatedResponse)
def read_arrivals(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（到货单号/物料编码）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    is_delayed: Optional[bool] = Query(None, description="是否延迟筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    到货跟踪列表
    """
    query = db.query(MaterialArrival)

    if keyword:
        query = query.filter(
            or_(
                MaterialArrival.arrival_no.like(f"%{keyword}%"),
                MaterialArrival.material_code.like(f"%{keyword}%")
            )
        )

    if status:
        query = query.filter(MaterialArrival.status == status)

    if supplier_id:
        query = query.filter(MaterialArrival.supplier_id == supplier_id)

    if is_delayed is not None:
        query = query.filter(MaterialArrival.is_delayed == is_delayed)

    total = query.count()
    offset = (page - 1) * page_size
    arrivals = query.order_by(desc(MaterialArrival.created_at)).offset(offset).limit(page_size).all()

    items = []
    for arrival in arrivals:
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
            supplier_name=arrival.supplier_name,
            expected_date=arrival.expected_date,
            actual_date=arrival.actual_date,
            is_delayed=arrival.is_delayed,
            delay_days=arrival.delay_days,
            status=arrival.status,
            received_qty=arrival.received_qty,
            received_by=arrival.received_by,
            received_at=arrival.received_at,
            follow_up_count=arrival.follow_up_count,
            remark=arrival.remark,
            created_at=arrival.created_at,
            updated_at=arrival.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/shortage/arrivals/{arrival_id}", response_model=MaterialArrivalResponse)
def read_arrival(
    arrival_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取到货跟踪详情
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

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
        supplier_name=arrival.supplier_name,
        expected_date=arrival.expected_date,
        actual_date=arrival.actual_date,
        is_delayed=arrival.is_delayed,
        delay_days=arrival.delay_days,
        status=arrival.status,
        received_qty=arrival.received_qty,
        received_by=arrival.received_by,
        received_at=arrival.received_at,
        follow_up_count=arrival.follow_up_count,
        remark=arrival.remark,
        created_at=arrival.created_at,
        updated_at=arrival.updated_at,
    )


@router.put("/shortage/arrivals/{arrival_id}/status", response_model=MaterialArrivalResponse)
def update_arrival_status(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    status: str = Body(..., description="新状态"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新到货跟踪状态
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    valid_statuses = ['PENDING', 'IN_TRANSIT', 'DELAYED', 'RECEIVED', 'CANCELLED']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效的状态，允许的状态：{', '.join(valid_statuses)}")

    arrival.status = status

    # 如果状态为在途，检查是否延迟
    if status == 'IN_TRANSIT':
        today = date.today()
        if arrival.expected_date < today:
            arrival.is_delayed = True
            arrival.delay_days = (today - arrival.expected_date).days
            arrival.status = 'DELAYED'

    db.add(arrival)
    db.commit()
    db.refresh(arrival)

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
        supplier_name=arrival.supplier_name,
        expected_date=arrival.expected_date,
        actual_date=arrival.actual_date,
        is_delayed=arrival.is_delayed,
        delay_days=arrival.delay_days,
        status=arrival.status,
        received_qty=arrival.received_qty,
        received_by=arrival.received_by,
        received_at=arrival.received_at,
        follow_up_count=arrival.follow_up_count,
        remark=arrival.remark,
        created_at=arrival.created_at,
        updated_at=arrival.updated_at,
    )


@router.get("/shortage/arrivals/delayed", response_model=PaginatedResponse)
def get_delayed_arrivals(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    延迟到货列表
    获取所有延迟的到货跟踪记录，用于预警
    """
    # 查询延迟的到货记录
    query = db.query(MaterialArrival).filter(
        MaterialArrival.is_delayed == True,
        MaterialArrival.status.in_(['PENDING', 'IN_TRANSIT', 'DELAYED']),  # 未收货的延迟记录
    )

    if supplier_id:
        query = query.filter(MaterialArrival.supplier_id == supplier_id)

    total = query.count()
    offset = (page - 1) * page_size
    arrivals = query.order_by(
        MaterialArrival.delay_days.desc(),  # 按延迟天数降序
        MaterialArrival.expected_date
    ).offset(offset).limit(page_size).all()

    items = []
    for arrival in arrivals:
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
            supplier_name=arrival.supplier_name,
            expected_date=arrival.expected_date,
            actual_date=arrival.actual_date,
            is_delayed=arrival.is_delayed,
            delay_days=arrival.delay_days,
            status=arrival.status,
            received_qty=arrival.received_qty,
            received_by=arrival.received_by,
            received_at=arrival.received_at,
            follow_up_count=arrival.follow_up_count,
            remark=arrival.remark,
            created_at=arrival.created_at,
            updated_at=arrival.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/shortage/arrivals/{arrival_id}/receive", response_model=MaterialArrivalResponse)
def receive_arrival(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    received_qty: Decimal = Body(..., description="实收数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认收货
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    arrival.status = 'RECEIVED'
    arrival.received_qty = received_qty
    arrival.received_by = current_user.id
    arrival.received_at = datetime.now()
    arrival.actual_date = date.today()

    # 检查是否延迟
    if arrival.expected_date < arrival.actual_date:
        arrival.is_delayed = True
        arrival.delay_days = (arrival.actual_date - arrival.expected_date).days

    db.add(arrival)
    db.commit()
    db.refresh(arrival)

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
        supplier_name=arrival.supplier_name,
        expected_date=arrival.expected_date,
        actual_date=arrival.actual_date,
        is_delayed=arrival.is_delayed,
        delay_days=arrival.delay_days,
        status=arrival.status,
        received_qty=arrival.received_qty,
        received_by=arrival.received_by,
        received_at=arrival.received_at,
        follow_up_count=arrival.follow_up_count,
        remark=arrival.remark,
        created_at=arrival.created_at,
        updated_at=arrival.updated_at,
    )
