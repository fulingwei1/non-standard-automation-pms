# -*- coding: utf-8 -*-
"""
缺料上报 - 自动生成
从 shortage.py 拆分
"""

# -*- coding: utf-8 -*-
"""
缺料管理 API endpoints
包含：缺料上报、到货跟踪、物料替代、物料调拨、缺料统计
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import require_shortage_report_access
from app.models.machine import Machine
from app.models.material import Material
from app.models.project import Project
from app.models.purchase import PurchaseOrder
from app.models.shortage import (
    ArrivalFollowUp,
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageDailyReport,
    ShortageReport,
)
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.shortage import (
    ArrivalFollowUpCreate,
    ArrivalFollowUpResponse,
    MaterialArrivalCreate,
    MaterialArrivalResponse,
    MaterialSubstitutionCreate,
    MaterialSubstitutionResponse,
    MaterialTransferCreate,
    MaterialTransferResponse,
    ShortageReportCreate,
    ShortageReportResponse,
)

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
    from app.models.shortage import ShortageReport
    from app.utils.number_generator import generate_sequential_no

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
    from app.models.shortage import MaterialArrival
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


def generate_substitution_no(db: Session) -> str:
    """生成替代单号：SUB-yymmdd-xxx"""
    from app.models.shortage import MaterialSubstitution
    from app.utils.number_generator import generate_sequential_no

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
    from app.models.shortage import MaterialTransfer
    from app.utils.number_generator import generate_sequential_no

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
    prefix="/shortage/reports",
    tags=["reports"]
)

# 共 7 个路由

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


