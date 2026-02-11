# -*- coding: utf-8 -*-
"""
到货跟踪 - arrivals.py

合并来源:
- app/api/v1/endpoints/shortage/arrival_crud.py
- app/api/v1/endpoints/shortage/arrival_follow_ups.py
- app/api/v1/endpoints/shortage/arrival_helpers.py
- app/api/v1/endpoints/shortage_alerts/arrivals.py

路由:
- GET    /                          到货列表
- POST   /                          创建到货记录
- GET    /{id}                      到货详情
- PUT    /{id}/status               更新状态
- POST   /{id}/follow-up            创建跟催
- GET    /{id}/follow-ups           跟催记录列表
- POST   /{id}/receive              确认收货
- GET    /delayed                   延迟到货列表
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.core.config import settings
from app.models.material import Material
from app.models.vendor import Vendor
from app.models.purchase import PurchaseOrder
from app.models.shortage import ArrivalFollowUp, MaterialArrival, ShortageReport
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.shortage import (
    ArrivalFollowUpCreate,
    ArrivalFollowUpResponse,
    MaterialArrivalCreate,
    MaterialArrivalResponse,
)

router = APIRouter()


# ============================================================
# 工具函数
# ============================================================

def _generate_arrival_no(db: Session) -> str:
    """生成到货跟踪单号：ARR-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialArrival,
        no_field='arrival_no',
        prefix='ARR',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def _build_arrival_response(arrival: MaterialArrival) -> MaterialArrivalResponse:
    """构建到货响应对象"""
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


# ============================================================
# CRUD 操作
# ============================================================

@router.get("", response_model=PaginatedResponse)
def list_arrivals(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（到货单号/物料编码）"),
    arrival_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    is_delayed: Optional[bool] = Query(None, description="是否延迟筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """到货跟踪列表"""
    query = db.query(MaterialArrival)

    # 应用关键词过滤（到货单号/物料编码）
    query = apply_keyword_filter(query, MaterialArrival, keyword, ["arrival_no", "material_code"])

    if arrival_status:
        query = query.filter(MaterialArrival.status == arrival_status)
    if supplier_id:
        query = query.filter(MaterialArrival.supplier_id == supplier_id)
    if is_delayed is not None:
        query = query.filter(MaterialArrival.is_delayed == is_delayed)

    total = query.count()
    arrivals = apply_pagination(query.order_by(desc(MaterialArrival.created_at)), pagination.offset, pagination.limit).all()

    items = [_build_arrival_response(arrival) for arrival in arrivals]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("", response_model=MaterialArrivalResponse, status_code=status.HTTP_201_CREATED)
def create_arrival(
    *,
    db: Session = Depends(deps.get_db),
    arrival_in: MaterialArrivalCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建到货跟踪（从采购订单或缺料上报创建）"""
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
        supplier = db.query(Vendor).filter(Vendor.id == arrival_in.supplier_id, Vendor.vendor_type == 'MATERIAL').first()
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")

    arrival = MaterialArrival(
        arrival_no=_generate_arrival_no(db),
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

    return _build_arrival_response(arrival)


@router.get("/delayed", response_model=PaginatedResponse)
def get_delayed_arrivals(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """延迟到货列表"""
    query = db.query(MaterialArrival).filter(
        MaterialArrival.is_delayed == True,
        MaterialArrival.status.in_(['PENDING', 'IN_TRANSIT', 'DELAYED']),
    )

    if supplier_id:
        query = query.filter(MaterialArrival.supplier_id == supplier_id)

    total = query.count()
    arrivals = query.order_by(
        MaterialArrival.delay_days.desc(),
        MaterialArrival.expected_date
    ).offset(pagination.offset).limit(pagination.limit).all()

    items = [_build_arrival_response(arrival) for arrival in arrivals]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/{arrival_id}", response_model=MaterialArrivalResponse)
def get_arrival(
    arrival_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """到货详情"""
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    return _build_arrival_response(arrival)


# ============================================================
# 状态操作
# ============================================================

@router.put("/{arrival_id}/status", response_model=MaterialArrivalResponse)
def update_arrival_status(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    status: str = Body(..., description="新状态"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新到货状态"""
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

    return _build_arrival_response(arrival)


@router.post("/{arrival_id}/receive", response_model=MaterialArrivalResponse)
def receive_arrival(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    received_qty: Decimal = Body(..., description="实收数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """确认收货"""
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

    return _build_arrival_response(arrival)


# ============================================================
# 跟催管理
# ============================================================

@router.get("/{arrival_id}/follow-ups", response_model=PaginatedResponse)
def list_arrival_follow_ups(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """到货跟踪的跟催记录列表"""
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    query = db.query(ArrivalFollowUp).filter(ArrivalFollowUp.arrival_id == arrival_id)

    total = query.count()
    follow_ups = apply_pagination(query.order_by(desc(ArrivalFollowUp.followed_at)), pagination.offset, pagination.limit).all()

    items = []
    for follow_up in follow_ups:
        followed_by_user = db.query(User).filter(User.id == follow_up.followed_by).first()
        items.append(ArrivalFollowUpResponse(
            id=follow_up.id,
            arrival_id=follow_up.arrival_id,
            follow_up_type=follow_up.follow_up_type,
            follow_up_note=follow_up.follow_up_note,
            followed_by=follow_up.followed_by,
            followed_by_name=followed_by_user.real_name or followed_by_user.username if followed_by_user else None,
            followed_at=follow_up.followed_at,
            supplier_response=follow_up.supplier_response,
            next_follow_up_date=follow_up.next_follow_up_date,
            created_at=follow_up.created_at,
            updated_at=follow_up.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/{arrival_id}/follow-up", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    follow_up_in: ArrivalFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建跟催记录"""
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    follow_up = ArrivalFollowUp(
        arrival_id=arrival_id,
        follow_up_type=follow_up_in.follow_up_type,
        follow_up_note=follow_up_in.follow_up_note,
        followed_by=current_user.id,
        followed_at=datetime.now(),
        supplier_response=follow_up_in.supplier_response,
        next_follow_up_date=follow_up_in.next_follow_up_date
    )

    # 更新到货跟踪的跟催信息
    arrival.follow_up_count = (arrival.follow_up_count or 0) + 1
    arrival.last_follow_up_at = datetime.now()

    db.add(follow_up)
    db.add(arrival)
    db.commit()

    return ResponseModel(code=200, message="跟催记录创建成功")
