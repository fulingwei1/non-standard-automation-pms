# -*- coding: utf-8 -*-
"""
到货跟踪 - 自动生成
从 shortage.py 拆分
"""

# -*- coding: utf-8 -*-
"""
缺料管理 API endpoints
包含：缺料上报、到货跟踪、物料替代、物料调拨、缺料统计
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import require_shortage_report_access
from app.models.user import User
from app.models.project import Project
from app.models.machine import Machine
from app.models.material import Material
from app.models.supplier import Supplier
from app.models.purchase import PurchaseOrder
from app.models.shortage import (
    ShortageReport, MaterialArrival, ArrivalFollowUp,
    MaterialSubstitution, MaterialTransfer, ShortageDailyReport
)
from app.schemas.shortage import (
    ShortageReportCreate, ShortageReportResponse,
    MaterialArrivalCreate, MaterialArrivalResponse,
    ArrivalFollowUpCreate, ArrivalFollowUpResponse,
    MaterialSubstitutionCreate, MaterialSubstitutionResponse,
    MaterialTransferCreate, MaterialTransferResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def _build_shortage_daily_report(report: ShortageDailyReport) -> Dict[str, Any]:
    """序列化缺料日报"""
    return {
        "date": report.report_date.isoformat(),
        "alerts": {
            "new": report.new_alerts,
            "resolved": report.resolved_alerts,
            "pending": report.pending_alerts,
            "overdue": report.overdue_alerts,
            "levels": {
                "level1": report.level1_count,
                "level2": report.level2_count,
                "level3": report.level3_count,
                "level4": report.level4_count,
            }
        },
        "reports": {
            "new": report.new_reports,
            "resolved": report.resolved_reports,
        },
        "kit": {
            "total_work_orders": report.total_work_orders,
            "complete_count": report.kit_complete_count,
            "kit_rate": float(report.kit_rate) if report.kit_rate else 0.0,
        },
        "arrivals": {
            "expected": report.expected_arrivals,
            "actual": report.actual_arrivals,
            "delayed": report.delayed_arrivals,
            "on_time_rate": float(report.on_time_rate) if report.on_time_rate else 0.0,
        },
        "response": {
            "avg_response_minutes": report.avg_response_minutes,
            "avg_resolve_hours": float(report.avg_resolve_hours) if report.avg_resolve_hours else 0.0,
        },
        "stoppage": {
            "count": report.stoppage_count,
            "hours": float(report.stoppage_hours) if report.stoppage_hours else 0.0,
        },
    }


def generate_report_no(db: Session) -> str:
    """生成缺料上报单号：SR-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.shortage import ShortageReport
    
    return generate_sequential_no(
        db=db,
        model_class=ShortageReport,
        no_field='report_no',
        prefix='SR',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_arrival_no(db: Session) -> str:
    """生成到货跟踪单号：ARR-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.shortage import MaterialArrival
    
    return generate_sequential_no(
        db=db,
        model_class=MaterialArrival,
        no_field='arrival_no',
        prefix='ARR',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_substitution_no(db: Session) -> str:
    """生成替代单号：SUB-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.shortage import MaterialSubstitution
    
    return generate_sequential_no(
        db=db,
        model_class=MaterialSubstitution,
        no_field='substitution_no',
        prefix='SUB',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_transfer_no(db: Session) -> str:
    """生成调拨单号：TRF-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.shortage import MaterialTransfer
    
    return generate_sequential_no(
        db=db,
        model_class=MaterialTransfer,
        no_field='transfer_no',
        prefix='TRF',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )




from fastapi import APIRouter

router = APIRouter(
    prefix="/shortage/arrivals",
    tags=["arrivals"]
)

# 共 8 个路由

# ==================== 到货跟踪 ====================

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
                MaterialArrival.material_code.like(f"%{keyword}%"),
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
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    到货跟踪详情
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
    status: str = Body(..., description="状态"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新到货状态
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")
    
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


@router.get("/shortage/arrivals/{arrival_id}/follow-ups", response_model=PaginatedResponse)
def read_arrival_follow_ups(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取到货跟踪的跟催记录列表
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")
    
    query = db.query(ArrivalFollowUp).filter(ArrivalFollowUp.arrival_id == arrival_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    follow_ups = query.order_by(desc(ArrivalFollowUp.followed_at)).offset(offset).limit(page_size).all()
    
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
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/shortage/arrivals/{arrival_id}/follow-up", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    follow_up_in: ArrivalFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
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
    today = date.today()
    
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

