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


# ==================== 缺料上报 ====================

@router.get("/shortage/reports", response_model=PaginatedResponse)
def read_shortage_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（上报单号/物料编码/物料名称）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    material_id: Optional[int] = Query(None, description="物料ID筛选"),
    urgent_level: Optional[str] = Query(None, description="紧急程度筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料上报列表
    """
    query = db.query(ShortageReport)
    
    if keyword:
        query = query.filter(
            or_(
                ShortageReport.report_no.like(f"%{keyword}%"),
                ShortageReport.material_code.like(f"%{keyword}%"),
                ShortageReport.material_name.like(f"%{keyword}%"),
            )
        )
    
    if status:
        query = query.filter(ShortageReport.status == status)
    
    if project_id:
        query = query.filter(ShortageReport.project_id == project_id)
    
    if material_id:
        query = query.filter(ShortageReport.material_id == material_id)
    
    if urgent_level:
        query = query.filter(ShortageReport.urgent_level == urgent_level)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(ShortageReport.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        machine = db.query(Machine).filter(Machine.id == report.machine_id).first() if report.machine_id else None
        reporter = db.query(User).filter(User.id == report.reporter_id).first()
        
        items.append(ShortageReportResponse(
            id=report.id,
            report_no=report.report_no,
            project_id=report.project_id,
            project_name=project.project_name if project else None,
            machine_id=report.machine_id,
            machine_name=machine.machine_name if machine else None,
            work_order_id=report.work_order_id,
            material_id=report.material_id,
            material_code=report.material_code,
            material_name=report.material_name,
            required_qty=report.required_qty,
            shortage_qty=report.shortage_qty,
            urgent_level=report.urgent_level,
            status=report.status,
            reporter_id=report.reporter_id,
            reporter_name=reporter.real_name or reporter.username if reporter else None,
            report_time=report.report_time,
            confirmed_by=report.confirmed_by,
            confirmed_at=report.confirmed_at,
            handler_id=report.handler_id,
            resolved_at=report.resolved_at,
            solution_type=report.solution_type,
            solution_note=report.solution_note,
            remark=report.remark,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/shortage/reports", response_model=ShortageReportResponse, status_code=status.HTTP_201_CREATED)
def create_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: ShortageReportCreate,
    current_user: User = Depends(require_shortage_report_access),
) -> Any:
    """
    创建缺料上报（车间扫码上报）
    权限：装配技工、装配钳工、装配电工、仓库管理员、PMC计划员等
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == report_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证物料
    material = db.query(Material).filter(Material.id == report_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    report = ShortageReport(
        report_no=generate_report_no(db),
        project_id=report_in.project_id,
        machine_id=report_in.machine_id,
        work_order_id=report_in.work_order_id,
        material_id=report_in.material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        required_qty=report_in.required_qty,
        shortage_qty=report_in.shortage_qty,
        urgent_level=report_in.urgent_level,
        status='REPORTED',
        reporter_id=current_user.id,
        report_time=datetime.now(),
        report_location=report_in.report_location,
        remark=report_in.remark
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    project = db.query(Project).filter(Project.id == report.project_id).first()
    machine = db.query(Machine).filter(Machine.id == report.machine_id).first() if report.machine_id else None
    reporter = db.query(User).filter(User.id == report.reporter_id).first()
    
    return ShortageReportResponse(
        id=report.id,
        report_no=report.report_no,
        project_id=report.project_id,
        project_name=project.project_name if project else None,
        machine_id=report.machine_id,
        machine_name=machine.machine_name if machine else None,
        work_order_id=report.work_order_id,
        material_id=report.material_id,
        material_code=report.material_code,
        material_name=report.material_name,
        required_qty=report.required_qty,
        shortage_qty=report.shortage_qty,
        urgent_level=report.urgent_level,
        status=report.status,
        reporter_id=report.reporter_id,
        reporter_name=reporter.real_name or reporter.username if reporter else None,
        report_time=report.report_time,
        confirmed_by=report.confirmed_by,
        confirmed_at=report.confirmed_at,
        handler_id=report.handler_id,
        resolved_at=report.resolved_at,
        solution_type=report.solution_type,
        solution_note=report.solution_note,
        remark=report.remark,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/shortage/reports/{report_id}", response_model=ShortageReportResponse)
def read_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上报详情
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    project = db.query(Project).filter(Project.id == report.project_id).first()
    machine = db.query(Machine).filter(Machine.id == report.machine_id).first() if report.machine_id else None
    reporter = db.query(User).filter(User.id == report.reporter_id).first()
    
    return ShortageReportResponse(
        id=report.id,
        report_no=report.report_no,
        project_id=report.project_id,
        project_name=project.project_name if project else None,
        machine_id=report.machine_id,
        machine_name=machine.machine_name if machine else None,
        work_order_id=report.work_order_id,
        material_id=report.material_id,
        material_code=report.material_code,
        material_name=report.material_name,
        required_qty=report.required_qty,
        shortage_qty=report.shortage_qty,
        urgent_level=report.urgent_level,
        status=report.status,
        reporter_id=report.reporter_id,
        reporter_name=reporter.real_name or reporter.username if reporter else None,
        report_time=report.report_time,
        confirmed_by=report.confirmed_by,
        confirmed_at=report.confirmed_at,
        handler_id=report.handler_id,
        resolved_at=report.resolved_at,
        solution_type=report.solution_type,
        solution_note=report.solution_note,
        remark=report.remark,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.put("/shortage/reports/{report_id}/confirm", response_model=ShortageReportResponse)
def confirm_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认上报（仓管确认）
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status != 'REPORTED':
        raise HTTPException(status_code=400, detail="只有已上报状态的记录才能确认")
    
    report.status = 'CONFIRMED'
    report.confirmed_by = current_user.id
    report.confirmed_at = datetime.now()
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(db=db, report_id=report_id, current_user=current_user)


@router.put("/shortage/reports/{report_id}/handle", response_model=ShortageReportResponse)
def handle_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    solution_type: str = Body(..., description="解决方案类型"),
    solution_note: Optional[str] = Body(None, description="解决方案说明"),
    handler_id: Optional[int] = Body(None, description="处理人ID（默认当前用户）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    处理上报
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status not in ['CONFIRMED', 'HANDLING']:
        raise HTTPException(status_code=400, detail="只有已确认或处理中的记录才能处理")
    
    report.status = 'HANDLING'
    report.handler_id = handler_id or current_user.id
    report.solution_type = solution_type
    report.solution_note = solution_note
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(db=db, report_id=report_id, current_user=current_user)


@router.put("/shortage/reports/{report_id}/resolve", response_model=ShortageReportResponse)
def resolve_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    解决上报
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status != 'HANDLING':
        raise HTTPException(status_code=400, detail="只有处理中的记录才能标记为已解决")
    
    report.status = 'RESOLVED'
    report.resolved_at = datetime.now()
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(db=db, report_id=report_id, current_user=current_user)


@router.put("/shortage/reports/{report_id}/reject", response_model=ShortageReportResponse)
def reject_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    reject_reason: Optional[str] = Body(None, description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    驳回上报
    用于驳回无效或错误的缺料上报
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status in ['RESOLVED', 'REJECTED']:
        raise HTTPException(status_code=400, detail="已解决或已驳回的记录不能再次驳回")
    
    report.status = 'REJECTED'
    if reject_reason:
        report.solution_note = f"驳回原因：{reject_reason}"
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(db=db, report_id=report_id, current_user=current_user)


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


# ==================== 物料替代 ====================

@router.get("/shortage/substitutions", response_model=PaginatedResponse)
def read_substitutions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（替代单号/物料编码）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    替代申请列表
    """
    query = db.query(MaterialSubstitution)
    
    if keyword:
        query = query.filter(
            or_(
                MaterialSubstitution.substitution_no.like(f"%{keyword}%"),
                MaterialSubstitution.original_material_code.like(f"%{keyword}%"),
                MaterialSubstitution.substitute_material_code.like(f"%{keyword}%"),
            )
        )
    
    if status:
        query = query.filter(MaterialSubstitution.status == status)
    
    if project_id:
        query = query.filter(MaterialSubstitution.project_id == project_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    substitutions = query.order_by(desc(MaterialSubstitution.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for sub in substitutions:
        project = db.query(Project).filter(Project.id == sub.project_id).first()
        tech_approver = db.query(User).filter(User.id == sub.tech_approver_id).first() if sub.tech_approver_id else None
        prod_approver = db.query(User).filter(User.id == sub.prod_approver_id).first() if sub.prod_approver_id else None
        
        items.append(MaterialSubstitutionResponse(
            id=sub.id,
            substitution_no=sub.substitution_no,
            project_id=sub.project_id,
            project_name=project.project_name if project else None,
            original_material_id=sub.original_material_id,
            original_material_code=sub.original_material_code,
            original_material_name=sub.original_material_name,
            original_qty=sub.original_qty,
            substitute_material_id=sub.substitute_material_id,
            substitute_material_code=sub.substitute_material_code,
            substitute_material_name=sub.substitute_material_name,
            substitute_qty=sub.substitute_qty,
            substitution_reason=sub.substitution_reason,
            technical_impact=sub.technical_impact,
            cost_impact=sub.cost_impact,
            status=sub.status,
            tech_approver_id=sub.tech_approver_id,
            tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
            tech_approved_at=sub.tech_approved_at,
            prod_approver_id=sub.prod_approver_id,
            prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
            prod_approved_at=sub.prod_approved_at,
            executed_at=sub.executed_at,
            remark=sub.remark,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/shortage/substitutions/{substitution_id}", response_model=MaterialSubstitutionResponse)
def read_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    替代申请详情
    """
    substitution = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == substitution_id).first()
    if not substitution:
        raise HTTPException(status_code=404, detail="替代申请不存在")
    
    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    tech_approver = db.query(User).filter(User.id == substitution.tech_approver_id).first() if substitution.tech_approver_id else None
    prod_approver = db.query(User).filter(User.id == substitution.prod_approver_id).first() if substitution.prod_approver_id else None
    
    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


@router.post("/shortage/substitutions", response_model=MaterialSubstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_in: MaterialSubstitutionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建替代申请
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == substitution_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证物料
    original_material = db.query(Material).filter(Material.id == substitution_in.original_material_id).first()
    if not original_material:
        raise HTTPException(status_code=404, detail="原物料不存在")
    
    substitute_material = db.query(Material).filter(Material.id == substitution_in.substitute_material_id).first()
    if not substitute_material:
        raise HTTPException(status_code=404, detail="替代物料不存在")
    
    substitution = MaterialSubstitution(
        substitution_no=generate_substitution_no(db),
        shortage_report_id=substitution_in.shortage_report_id,
        project_id=substitution_in.project_id,
        bom_item_id=substitution_in.bom_item_id,
        original_material_id=substitution_in.original_material_id,
        original_material_code=original_material.material_code,
        original_material_name=original_material.material_name,
        original_qty=substitution_in.original_qty,
        substitute_material_id=substitution_in.substitute_material_id,
        substitute_material_code=substitute_material.material_code,
        substitute_material_name=substitute_material.material_name,
        substitute_qty=substitution_in.substitute_qty,
        substitution_reason=substitution_in.substitution_reason,
        technical_impact=substitution_in.technical_impact,
        cost_impact=substitution_in.cost_impact,
        status='DRAFT',
        created_by=current_user.id,
        remark=substitution_in.remark
    )
    
    db.add(substitution)
    db.commit()
    db.refresh(substitution)
    
    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    
    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


@router.put("/shortage/substitutions/{substitution_id}/tech-approve", response_model=MaterialSubstitutionResponse)
def tech_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    技术审批
    """
    substitution = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == substitution_id).first()
    if not substitution:
        raise HTTPException(status_code=404, detail="替代申请不存在")
    
    if substitution.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只有草稿状态的申请才能进行技术审批")
    
    if approved:
        substitution.status = 'TECH_APPROVED'
        substitution.tech_approver_id = current_user.id
        substitution.tech_approved_at = datetime.now()
        substitution.tech_approval_note = approval_note
        # 转为生产审批状态
        substitution.status = 'PROD_PENDING'
    else:
        substitution.status = 'REJECTED'
        substitution.tech_approver_id = current_user.id
        substitution.tech_approved_at = datetime.now()
        substitution.tech_approval_note = approval_note
    
    db.add(substitution)
    db.commit()
    db.refresh(substitution)
    
    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    tech_approver = db.query(User).filter(User.id == substitution.tech_approver_id).first() if substitution.tech_approver_id else None
    
    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


@router.put("/shortage/substitutions/{substitution_id}/prod-approve", response_model=MaterialSubstitutionResponse)
def prod_approve_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生产审批
    """
    substitution = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == substitution_id).first()
    if not substitution:
        raise HTTPException(status_code=404, detail="替代申请不存在")
    
    if substitution.status != 'PROD_PENDING':
        raise HTTPException(status_code=400, detail="只有待生产审批状态的申请才能进行生产审批")
    
    if approved:
        substitution.status = 'APPROVED'
        substitution.prod_approver_id = current_user.id
        substitution.prod_approved_at = datetime.now()
        substitution.prod_approval_note = approval_note
    else:
        substitution.status = 'REJECTED'
        substitution.prod_approver_id = current_user.id
        substitution.prod_approved_at = datetime.now()
        substitution.prod_approval_note = approval_note
    
    db.add(substitution)
    db.commit()
    db.refresh(substitution)
    
    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    tech_approver = db.query(User).filter(User.id == substitution.tech_approver_id).first() if substitution.tech_approver_id else None
    prod_approver = db.query(User).filter(User.id == substitution.prod_approver_id).first() if substitution.prod_approver_id else None
    
    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


@router.put("/shortage/substitutions/{substitution_id}/execute", response_model=MaterialSubstitutionResponse)
def execute_substitution(
    *,
    db: Session = Depends(deps.get_db),
    substitution_id: int,
    execution_note: Optional[str] = Body(None, description="执行说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行替代
    """
    substitution = db.query(MaterialSubstitution).filter(MaterialSubstitution.id == substitution_id).first()
    if not substitution:
        raise HTTPException(status_code=404, detail="替代申请不存在")
    
    if substitution.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只有已批准的申请才能执行")
    
    substitution.status = 'EXECUTED'
    substitution.executed_at = datetime.now()
    substitution.executed_by = current_user.id
    substitution.execution_note = execution_note
    
    # Note: 更新BOM或库存记录需要与BOM管理和库存管理系统集成
    # 如果substitution.bom_item_id存在，应更新对应BOM项的物料信息
    # 如果存在库存系统，应更新库存记录（减少原物料，增加替代物料）
    
    db.add(substitution)
    db.commit()
    db.refresh(substitution)
    
    project = db.query(Project).filter(Project.id == substitution.project_id).first()
    tech_approver = db.query(User).filter(User.id == substitution.tech_approver_id).first() if substitution.tech_approver_id else None
    prod_approver = db.query(User).filter(User.id == substitution.prod_approver_id).first() if substitution.prod_approver_id else None
    
    return MaterialSubstitutionResponse(
        id=substitution.id,
        substitution_no=substitution.substitution_no,
        project_id=substitution.project_id,
        project_name=project.project_name if project else None,
        original_material_id=substitution.original_material_id,
        original_material_code=substitution.original_material_code,
        original_material_name=substitution.original_material_name,
        original_qty=substitution.original_qty,
        substitute_material_id=substitution.substitute_material_id,
        substitute_material_code=substitution.substitute_material_code,
        substitute_material_name=substitution.substitute_material_name,
        substitute_qty=substitution.substitute_qty,
        substitution_reason=substitution.substitution_reason,
        technical_impact=substitution.technical_impact,
        cost_impact=substitution.cost_impact,
        status=substitution.status,
        tech_approver_id=substitution.tech_approver_id,
        tech_approver_name=tech_approver.real_name or tech_approver.username if tech_approver else None,
        tech_approved_at=substitution.tech_approved_at,
        prod_approver_id=substitution.prod_approver_id,
        prod_approver_name=prod_approver.real_name or prod_approver.username if prod_approver else None,
        prod_approved_at=substitution.prod_approved_at,
        executed_at=substitution.executed_at,
        remark=substitution.remark,
        created_at=substitution.created_at,
        updated_at=substitution.updated_at,
    )


# ==================== 物料调拨 ====================

@router.get("/shortage/transfers", response_model=PaginatedResponse)
def read_transfers(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（调拨单号/物料编码）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    from_project_id: Optional[int] = Query(None, description="调出项目ID筛选"),
    to_project_id: Optional[int] = Query(None, description="调入项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    调拨申请列表
    """
    query = db.query(MaterialTransfer)
    
    if keyword:
        query = query.filter(
            or_(
                MaterialTransfer.transfer_no.like(f"%{keyword}%"),
                MaterialTransfer.material_code.like(f"%{keyword}%"),
            )
        )
    
    if status:
        query = query.filter(MaterialTransfer.status == status)
    
    if from_project_id:
        query = query.filter(MaterialTransfer.from_project_id == from_project_id)
    
    if to_project_id:
        query = query.filter(MaterialTransfer.to_project_id == to_project_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    transfers = query.order_by(desc(MaterialTransfer.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for transfer in transfers:
        from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
        to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
        approver = db.query(User).filter(User.id == transfer.approver_id).first() if transfer.approver_id else None
        
        items.append(MaterialTransferResponse(
            id=transfer.id,
            transfer_no=transfer.transfer_no,
            from_project_id=transfer.from_project_id,
            from_project_name=from_project.project_name if from_project else None,
            from_location=transfer.from_location,
            to_project_id=transfer.to_project_id,
            to_project_name=to_project.project_name if to_project else None,
            to_location=transfer.to_location,
            material_id=transfer.material_id,
            material_code=transfer.material_code,
            material_name=transfer.material_name,
            transfer_qty=transfer.transfer_qty,
            available_qty=transfer.available_qty,
            transfer_reason=transfer.transfer_reason,
            urgent_level=transfer.urgent_level,
            status=transfer.status,
            approver_id=transfer.approver_id,
            approver_name=approver.real_name or approver.username if approver else None,
            approved_at=transfer.approved_at,
            executed_at=transfer.executed_at,
            actual_qty=transfer.actual_qty,
            remark=transfer.remark,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/shortage/transfers/{transfer_id}", response_model=MaterialTransferResponse)
def read_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    调拨申请详情
    """
    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="调拨申请不存在")
    
    from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    approver = db.query(User).filter(User.id == transfer.approver_id).first() if transfer.approver_id else None
    
    return MaterialTransferResponse(
        id=transfer.id,
        transfer_no=transfer.transfer_no,
        from_project_id=transfer.from_project_id,
        from_project_name=from_project.project_name if from_project else None,
        from_location=transfer.from_location,
        to_project_id=transfer.to_project_id,
        to_project_name=to_project.project_name if to_project else None,
        to_location=transfer.to_location,
        material_id=transfer.material_id,
        material_code=transfer.material_code,
        material_name=transfer.material_name,
        transfer_qty=transfer.transfer_qty,
        available_qty=transfer.available_qty,
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=approver.real_name or approver.username if approver else None,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.post("/shortage/transfers", response_model=MaterialTransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_in: MaterialTransferCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建调拨申请
    """
    # 验证调入项目
    to_project = db.query(Project).filter(Project.id == transfer_in.to_project_id).first()
    if not to_project:
        raise HTTPException(status_code=404, detail="调入项目不存在")
    
    # 验证物料
    material = db.query(Material).filter(Material.id == transfer_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    # Note: 检查可调拨数量需要与库存管理系统集成
    # 应查询from_project_id对应项目的可用库存（账面库存 - 已分配 - 安全库存）
    # 如果from_project_id为None，应从总库存中查询
    # 目前暂时设置为0，后续需要根据实际库存系统实现
    available_qty = Decimal("0")
    
    transfer = MaterialTransfer(
        transfer_no=generate_transfer_no(db),
        shortage_report_id=transfer_in.shortage_report_id,
        from_project_id=transfer_in.from_project_id,
        from_location=transfer_in.from_location,
        to_project_id=transfer_in.to_project_id,
        to_location=transfer_in.to_location,
        material_id=transfer_in.material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        transfer_qty=transfer_in.transfer_qty,
        available_qty=available_qty,
        transfer_reason=transfer_in.transfer_reason,
        urgent_level=transfer_in.urgent_level,
        status='DRAFT',
        created_by=current_user.id,
        remark=transfer_in.remark
    )
    
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    
    from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    
    return MaterialTransferResponse(
        id=transfer.id,
        transfer_no=transfer.transfer_no,
        from_project_id=transfer.from_project_id,
        from_project_name=from_project.project_name if from_project else None,
        from_location=transfer.from_location,
        to_project_id=transfer.to_project_id,
        to_project_name=to_project.project_name if to_project else None,
        to_location=transfer.to_location,
        material_id=transfer.material_id,
        material_code=transfer.material_code,
        material_name=transfer.material_name,
        transfer_qty=transfer.transfer_qty,
        available_qty=transfer.available_qty,
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=None,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.put("/shortage/transfers/{transfer_id}/approve", response_model=MaterialTransferResponse)
def approve_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    approved: bool = Body(..., description="是否批准"),
    approval_note: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    调拨审批
    """
    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="调拨申请不存在")
    
    if transfer.status not in ['DRAFT', 'PENDING']:
        raise HTTPException(status_code=400, detail="只有草稿或待审批状态的申请才能审批")
    
    if approved:
        transfer.status = 'APPROVED'
        transfer.approver_id = current_user.id
        transfer.approved_at = datetime.now()
        transfer.approval_note = approval_note
    else:
        transfer.status = 'REJECTED'
        transfer.approver_id = current_user.id
        transfer.approved_at = datetime.now()
        transfer.approval_note = approval_note
    
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    
    from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    approver = db.query(User).filter(User.id == transfer.approver_id).first() if transfer.approver_id else None
    
    return MaterialTransferResponse(
        id=transfer.id,
        transfer_no=transfer.transfer_no,
        from_project_id=transfer.from_project_id,
        from_project_name=from_project.project_name if from_project else None,
        from_location=transfer.from_location,
        to_project_id=transfer.to_project_id,
        to_project_name=to_project.project_name if to_project else None,
        to_location=transfer.to_location,
        material_id=transfer.material_id,
        material_code=transfer.material_code,
        material_name=transfer.material_name,
        transfer_qty=transfer.transfer_qty,
        available_qty=transfer.available_qty,
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=approver.real_name or approver.username if approver else None,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.put("/shortage/transfers/{transfer_id}/execute", response_model=MaterialTransferResponse)
def execute_transfer(
    *,
    db: Session = Depends(deps.get_db),
    transfer_id: int,
    actual_qty: Decimal = Body(..., description="实际调拨数量"),
    execution_note: Optional[str] = Body(None, description="执行说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行调拨
    """
    transfer = db.query(MaterialTransfer).filter(MaterialTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="调拨申请不存在")
    
    if transfer.status != 'APPROVED':
        raise HTTPException(status_code=400, detail="只有已批准的申请才能执行")
    
    transfer.status = 'EXECUTED'
    transfer.executed_at = datetime.now()
    transfer.executed_by = current_user.id
    transfer.actual_qty = actual_qty
    transfer.execution_note = execution_note
    
    # Note: 更新库存记录需要与库存管理系统集成
    # 应从from_project_id对应项目减少actual_qty数量的库存
    # 应向to_project_id对应项目增加actual_qty数量的库存
    # 如果from_project_id为None，应从总库存中减少
    
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    
    from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first() if transfer.from_project_id else None
    to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
    approver = db.query(User).filter(User.id == transfer.approver_id).first() if transfer.approver_id else None
    
    return MaterialTransferResponse(
        id=transfer.id,
        transfer_no=transfer.transfer_no,
        from_project_id=transfer.from_project_id,
        from_project_name=from_project.project_name if from_project else None,
        from_location=transfer.from_location,
        to_project_id=transfer.to_project_id,
        to_project_name=to_project.project_name if to_project else None,
        to_location=transfer.to_location,
        material_id=transfer.material_id,
        material_code=transfer.material_code,
        material_name=transfer.material_name,
        transfer_qty=transfer.transfer_qty,
        available_qty=transfer.available_qty,
        transfer_reason=transfer.transfer_reason,
        urgent_level=transfer.urgent_level,
        status=transfer.status,
        approver_id=transfer.approver_id,
        approver_name=approver.real_name or approver.username if approver else None,
        approved_at=transfer.approved_at,
        executed_at=transfer.executed_at,
        actual_qty=transfer.actual_qty,
        remark=transfer.remark,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


# ==================== 缺料统计 ====================

@router.get("/shortage/dashboard", response_model=ResponseModel)
def get_shortage_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料看板
    """
    # 统计缺料上报
    total_reports = db.query(ShortageReport).count()
    reported = db.query(ShortageReport).filter(ShortageReport.status == 'REPORTED').count()
    confirmed = db.query(ShortageReport).filter(ShortageReport.status == 'CONFIRMED').count()
    handling = db.query(ShortageReport).filter(ShortageReport.status == 'HANDLING').count()
    resolved = db.query(ShortageReport).filter(ShortageReport.status == 'RESOLVED').count()
    
    # 统计紧急缺料
    urgent_reports = db.query(ShortageReport).filter(
        ShortageReport.urgent_level.in_(['URGENT', 'CRITICAL']),
        ShortageReport.status != 'RESOLVED'
    ).count()
    
    # 统计到货跟踪
    total_arrivals = db.query(MaterialArrival).count()
    pending_arrivals = db.query(MaterialArrival).filter(MaterialArrival.status == 'PENDING').count()
    delayed_arrivals = db.query(MaterialArrival).filter(MaterialArrival.is_delayed == True).count()
    
    # 统计物料替代
    total_substitutions = db.query(MaterialSubstitution).count()
    pending_substitutions = db.query(MaterialSubstitution).filter(
        MaterialSubstitution.status.in_(['DRAFT', 'TECH_PENDING', 'PROD_PENDING'])
    ).count()
    
    # 统计物料调拨
    total_transfers = db.query(MaterialTransfer).count()
    pending_transfers = db.query(MaterialTransfer).filter(
        MaterialTransfer.status.in_(['DRAFT', 'PENDING'])
    ).count()
    
    # 最近缺料上报
    recent_reports = db.query(ShortageReport).order_by(desc(ShortageReport.created_at)).limit(10).all()
    recent_reports_list = []
    for report in recent_reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        recent_reports_list.append({
            'id': report.id,
            'report_no': report.report_no,
            'project_name': project.project_name if project else None,
            'material_name': report.material_name,
            'shortage_qty': float(report.shortage_qty),
            'urgent_level': report.urgent_level,
            'status': report.status,
            'report_time': report.report_time
        })
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "reports": {
                "total": total_reports,
                "reported": reported,
                "confirmed": confirmed,
                "handling": handling,
                "resolved": resolved,
                "urgent": urgent_reports
            },
            "arrivals": {
                "total": total_arrivals,
                "pending": pending_arrivals,
                "delayed": delayed_arrivals
            },
            "substitutions": {
                "total": total_substitutions,
                "pending": pending_substitutions
            },
            "transfers": {
                "total": total_transfers,
                "pending": pending_transfers
            },
            "recent_reports": recent_reports_list
        }
    )


@router.get("/shortage/supplier-delivery", response_model=ResponseModel)
def get_supplier_delivery_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    供应商交期分析
    """
    from datetime import timedelta
    
    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    query = db.query(MaterialArrival).filter(
        MaterialArrival.expected_date >= start_date,
        MaterialArrival.expected_date <= end_date
    )
    
    if supplier_id:
        query = query.filter(MaterialArrival.supplier_id == supplier_id)
    
    arrivals = query.all()
    
    # 按供应商统计
    supplier_stats = {}
    for arrival in arrivals:
        if arrival.supplier_id:
            supplier_key = f"{arrival.supplier_id}_{arrival.supplier_name}"
            if supplier_key not in supplier_stats:
                supplier_stats[supplier_key] = {
                    "supplier_id": arrival.supplier_id,
                    "supplier_name": arrival.supplier_name,
                    "total_orders": 0,
                    "on_time": 0,
                    "delayed": 0,
                    "avg_delay_days": 0.0
                }
            
            supplier_stats[supplier_key]["total_orders"] += 1
            if arrival.is_delayed:
                supplier_stats[supplier_key]["delayed"] += 1
                supplier_stats[supplier_key]["avg_delay_days"] += arrival.delay_days or 0
            else:
                supplier_stats[supplier_key]["on_time"] += 1
    
    # 计算平均延迟天数
    for key, stats in supplier_stats.items():
        if stats["delayed"] > 0:
            stats["avg_delay_days"] = round(stats["avg_delay_days"] / stats["delayed"], 2)
        stats["on_time_rate"] = round(stats["on_time"] / stats["total_orders"] * 100, 2) if stats["total_orders"] > 0 else 0.0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "supplier_stats": list(supplier_stats.values())
        }
    )


@router.get("/shortage/daily-report", response_model=ResponseModel)
def get_daily_report(
    db: Session = Depends(deps.get_db),
    report_date: Optional[date] = Query(None, description="报表日期（默认：今天）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料日报
    """
    if not report_date:
        report_date = date.today()
    
    # 统计当日缺料上报
    daily_reports = db.query(ShortageReport).filter(
        func.date(ShortageReport.report_time) == report_date
    ).all()
    
    # 按紧急程度统计
    by_urgent = {}
    for report in daily_reports:
        level = report.urgent_level
        if level not in by_urgent:
            by_urgent[level] = 0
        by_urgent[level] += 1
    
    # 按状态统计
    by_status = {}
    for report in daily_reports:
        status = report.status
        if status not in by_status:
            by_status[status] = 0
        by_status[status] += 1
    
    # 按物料统计
    by_material = {}
    for report in daily_reports:
        material_key = f"{report.material_id}_{report.material_name}"
        if material_key not in by_material:
            by_material[material_key] = {
                "material_id": report.material_id,
                "material_name": report.material_name,
                "count": 0,
                "total_shortage_qty": 0.0
            }
        by_material[material_key]["count"] += 1
        by_material[material_key]["total_shortage_qty"] += float(report.shortage_qty)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "report_date": str(report_date),
            "total_reports": len(daily_reports),
            "by_urgent": by_urgent,
            "by_status": by_status,
            "by_material": list(by_material.values())
        }
    )


@router.get("/shortage/daily-report/latest", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_latest_shortage_daily_report(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最新缺料日报（定时生成）
    """
    latest_date = db.query(func.max(ShortageDailyReport.report_date)).scalar()
    if not latest_date:
        return ResponseModel(data=None)
    
    report = db.query(ShortageDailyReport).filter(
        ShortageDailyReport.report_date == latest_date
    ).first()
    
    if not report:
        return ResponseModel(data=None)
    
    return ResponseModel(data=_build_shortage_daily_report(report))


@router.get("/shortage/daily-report/by-date", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_shortage_daily_report_by_date(
    *,
    db: Session = Depends(deps.get_db),
    report_date: date = Query(..., description="报表日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按日期获取缺料日报（定时生成的数据）
    """
    report = db.query(ShortageDailyReport).filter(
        ShortageDailyReport.report_date == report_date
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="指定日期不存在缺料日报")
    
    return ResponseModel(data=_build_shortage_daily_report(report))


@router.get("/shortage/cause-analysis", response_model=ResponseModel)
def get_cause_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料原因分析
    """
    from datetime import timedelta
    
    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    query = db.query(ShortageReport).filter(
        func.date(ShortageReport.report_time) >= start_date,
        func.date(ShortageReport.report_time) <= end_date
    )
    
    if project_id:
        query = query.filter(ShortageReport.project_id == project_id)
    
    reports = query.all()
    
    # 按解决方案类型统计
    by_solution = {}
    for report in reports:
        solution = report.solution_type or 'UNKNOWN'
        if solution not in by_solution:
            by_solution[solution] = {
                "solution_type": solution,
                "count": 0,
                "total_shortage_qty": 0.0,
                "avg_resolve_time": 0.0
            }
        by_solution[solution]["count"] += 1
        by_solution[solution]["total_shortage_qty"] += float(report.shortage_qty)
        
        # 计算平均解决时间
        if report.resolved_at and report.report_time:
            resolve_time = (report.resolved_at - report.report_time).total_seconds() / 3600  # 小时
            by_solution[solution]["avg_resolve_time"] += resolve_time
    
    # 计算平均解决时间
    for key, stats in by_solution.items():
        if stats["count"] > 0:
            stats["avg_resolve_time"] = round(stats["avg_resolve_time"] / stats["count"], 2)
    
    # 按紧急程度统计
    by_urgent = {}
    for report in reports:
        level = report.urgent_level
        if level not in by_urgent:
            by_urgent[level] = {
                "urgent_level": level,
                "count": 0,
                "total_shortage_qty": 0.0
            }
        by_urgent[level]["count"] += 1
        by_urgent[level]["total_shortage_qty"] += float(report.shortage_qty)
    
    # 按项目统计
    by_project = {}
    for report in reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        project_name = project.project_name if project else f"项目{report.project_id}"
        if project_name not in by_project:
            by_project[project_name] = {
                "project_id": report.project_id,
                "project_name": project_name,
                "count": 0,
                "total_shortage_qty": 0.0
            }
        by_project[project_name]["count"] += 1
        by_project[project_name]["total_shortage_qty"] += float(report.shortage_qty)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_reports": len(reports),
            "by_solution": list(by_solution.values()),
            "by_urgent": list(by_urgent.values()),
            "by_project": list(by_project.values())
        }
    )


@router.get("/shortage/statistics/kit-rate", response_model=ResponseModel)
def get_kit_rate_statistics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: Optional[str] = Query("project", description="分组方式: project/workshop/day"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    齐套率统计
    按项目/车间/时间维度统计齐套率
    """
    from app.services.kit_rate_statistics_service import (
        calculate_date_range,
        calculate_project_kit_statistics,
        calculate_workshop_kit_statistics,
        calculate_daily_kit_statistics,
        calculate_summary_statistics
    )
    
    # 默认使用当前月
    today = date.today()
    if not start_date or not end_date:
        default_start, default_end = calculate_date_range(today)
        start_date = start_date or default_start
        end_date = end_date or default_end
    
    # 获取项目列表
    query = db.query(Project).filter(Project.is_active == True)
    if project_id:
        query = query.filter(Project.id == project_id)
    projects = query.all()
    
    statistics = []
    
    if group_by == "project":
        # 按项目统计
        for project in projects:
            stat = calculate_project_kit_statistics(db, project)
            if stat:
                statistics.append(stat)
    
    elif group_by == "workshop":
        # 按车间统计
        statistics = calculate_workshop_kit_statistics(db, workshop_id, projects)
    
    elif group_by == "day":
        # 按日期统计
        statistics = calculate_daily_kit_statistics(db, start_date, end_date, projects)
    
    # 计算汇总
    summary = calculate_summary_statistics(statistics, group_by)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "group_by": group_by,
            "statistics": statistics,
            "summary": summary
        }
    )
