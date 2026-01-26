# -*- coding: utf-8 -*-
"""
缺料上报 - reports.py

合并来源:
- app/api/v1/endpoints/shortage/reports/crud.py
- app/api/v1/endpoints/shortage/reports/operations.py
- app/api/v1/endpoints/shortage/reports/utils.py
- app/api/v1/endpoints/shortage_alerts/reports.py

路由:
- GET    /                  上报列表
- POST   /                  创建上报
- GET    /{id}              上报详情
- PUT    /{id}/confirm      确认
- PUT    /{id}/handle       处理中
- PUT    /{id}/resolve      解决
- PUT    /{id}/reject       驳回
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.machine import Machine
from app.models.material import Material
from app.models.project import Project
from app.models.shortage import ShortageReport
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.shortage import ShortageReportCreate, ShortageReportResponse

router = APIRouter()


# ============================================================
# 工具函数
# ============================================================

def _generate_report_no(db: Session) -> str:
    """生成缺料上报单号：SR-yymmdd-xxx"""
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


def _build_report_response(report: ShortageReport, db: Session) -> ShortageReportResponse:
    """构建上报响应对象"""
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


# ============================================================
# CRUD 操作
# ============================================================

@router.get("", response_model=PaginatedResponse)
def list_shortage_reports(
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
    """缺料上报列表"""
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

    items = [_build_report_response(report, db) for report in reports]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("", response_model=ShortageReportResponse, status_code=status.HTTP_201_CREATED)
def create_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: ShortageReportCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建缺料上报（车间扫码上报）"""
    # 验证项目
    project = db.query(Project).filter(Project.id == report_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证机台（如果提供）
    if report_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == report_in.machine_id).first()
        if not machine or machine.project_id != report_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")

    # 验证物料
    material = db.query(Material).filter(Material.id == report_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    report = ShortageReport(
        report_no=_generate_report_no(db),
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

    return _build_report_response(report, db)


@router.get("/{report_id}", response_model=ShortageReportResponse)
def get_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """上报详情"""
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")

    return _build_report_response(report, db)


# ============================================================
# 状态操作
# ============================================================

@router.put("/{report_id}/confirm", response_model=ShortageReportResponse)
def confirm_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """确认上报（仓管确认）"""
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

    return _build_report_response(report, db)


@router.put("/{report_id}/handle", response_model=ShortageReportResponse)
def handle_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    solution_type: str = Body(..., description="解决方案类型：PURCHASE/SUBSTITUTE/TRANSFER/OTHER"),
    solution_note: Optional[str] = Body(None, description="解决方案说明"),
    handler_id: Optional[int] = Body(None, description="处理人ID（默认当前用户）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """处理上报"""
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

    return _build_report_response(report, db)


@router.put("/{report_id}/resolve", response_model=ShortageReportResponse)
def resolve_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """解决上报"""
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")

    if report.status != 'HANDLING':
        raise HTTPException(status_code=400, detail="只有处理中的记录才能标记为已解决")

    report.status = 'RESOLVED'
    report.resolved_at = datetime.now()
    if not report.handler_id:
        report.handler_id = current_user.id

    db.add(report)
    db.commit()
    db.refresh(report)

    return _build_report_response(report, db)


@router.put("/{report_id}/reject", response_model=ShortageReportResponse)
def reject_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    reject_reason: Optional[str] = Body(None, description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """驳回上报（用于驳回无效或错误的缺料上报）"""
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

    return _build_report_response(report, db)
