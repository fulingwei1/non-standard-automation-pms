# -*- coding: utf-8 -*-
"""
缺料上报 - 自动生成
从 shortage_alerts.py 拆分
"""

from typing import Any, List, Optional

from datetime import date, datetime

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from sqlalchemy.orm import Session

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.material import MaterialShortage, Material, BomItem

from app.models.project import Project, Machine

from app.models.shortage import (
    ShortageReport,
    MaterialArrival,
    ArrivalFollowUp,
    MaterialSubstitution,
    MaterialTransfer,
)
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.production import WorkOrder
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.shortage import (
    ShortageReportCreate,
    ShortageReportResponse,
    ShortageReportListResponse,
    MaterialArrivalResponse,
    MaterialArrivalListResponse,
    ArrivalFollowUpCreate,
    MaterialSubstitutionCreate,
    MaterialSubstitutionResponse,
    MaterialSubstitutionListResponse,
    MaterialTransferCreate,
    MaterialTransferResponse,
    MaterialTransferListResponse,
)

router = APIRouter(tags=["reports"])

# 共 6 个路由

@router.get("/reports", response_model=PaginatedResponse, status_code=200)
def read_shortage_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    urgent_level: Optional[str] = Query(None, description="紧急程度筛选"),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    缺料上报列表
    """
    query = db.query(ShortageReport)
    
    if project_id:
        query = query.filter(ShortageReport.project_id == project_id)
    if status:
        query = query.filter(ShortageReport.status == status)
    if urgent_level:
        query = query.filter(ShortageReport.urgent_level == urgent_level)
    
    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(desc(ShortageReport.report_time)).offset(offset).limit(page_size).all()
    
    items = []
    for report in reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        machine = None
        if report.machine_id:
            machine = db.query(Machine).filter(Machine.id == report.machine_id).first()
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
            updated_at=report.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/reports", response_model=ShortageReportResponse, status_code=201)
def create_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: ShortageReportCreate,
    current_user: User = Depends(security.require_permission("shortage_alert:create")),
) -> Any:
    """
    创建缺料上报（车间扫码上报）
    """
    project = db.query(Project).filter(Project.id == report_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if report_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == report_in.machine_id).first()
        if not machine or machine.project_id != report_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")
    
    material = db.query(Material).filter(Material.id == report_in.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    
    report_no = generate_shortage_report_no(db)
    
    report = ShortageReport(
        report_no=report_no,
        project_id=report_in.project_id,
        machine_id=report_in.machine_id,
        work_order_id=report_in.work_order_id,
        material_id=report_in.material_id,
        material_code=material.material_code,
        material_name=material.material_name,
        required_qty=report_in.required_qty,
        shortage_qty=report_in.shortage_qty,
        urgent_level=report_in.urgent_level,
        status="REPORTED",
        reporter_id=current_user.id,
        report_location=report_in.report_location,
        remark=report_in.remark
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(report.id, db, current_user)


@router.get("/reports/{report_id}", response_model=ShortageReportResponse, status_code=200)
def read_shortage_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("shortage_alert:read")),
) -> Any:
    """
    上报详情
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    project = db.query(Project).filter(Project.id == report.project_id).first()
    machine = None
    if report.machine_id:
        machine = db.query(Machine).filter(Machine.id == report.machine_id).first()
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
        updated_at=report.updated_at
    )


@router.put("/reports/{report_id}/confirm", response_model=ShortageReportResponse, status_code=200)
def confirm_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    确认上报（仓管确认）
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status != "REPORTED":
        raise HTTPException(status_code=400, detail="只能确认已上报状态的记录")
    
    report.status = "CONFIRMED"
    report.confirmed_by = current_user.id
    report.confirmed_at = datetime.now()
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(report_id, db, current_user)


@router.put("/reports/{report_id}/handle", response_model=ShortageReportResponse, status_code=200)
def handle_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    solution_type: str = Query(..., description="解决方案类型：PURCHASE/SUBSTITUTE/TRANSFER/OTHER"),
    solution_note: Optional[str] = Query(None, description="解决方案说明"),
    handler_id: Optional[int] = Query(None, description="处理人ID"),
    current_user: User = Depends(security.require_permission("shortage_alert:update")),
) -> Any:
    """
    处理上报
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status not in ["CONFIRMED", "HANDLING"]:
        raise HTTPException(status_code=400, detail="只能处理已确认或处理中状态的记录")
    
    report.status = "HANDLING"
    report.solution_type = solution_type
    report.solution_note = solution_note
    report.handler_id = handler_id or current_user.id
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(report_id, db, current_user)


@router.put("/reports/{report_id}/resolve", response_model=ShortageReportResponse, status_code=200)
def resolve_shortage_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.require_permission("shortage_alert:resolve")),
) -> Any:
    """
    解决上报
    """
    report = db.query(ShortageReport).filter(ShortageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="缺料上报不存在")
    
    if report.status != "HANDLING":
        raise HTTPException(status_code=400, detail="只能解决处理中状态的记录")
    
    report.status = "RESOLVED"
    report.resolved_at = datetime.now()
    if not report.handler_id:
        report.handler_id = current_user.id
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return read_shortage_report(report_id, db, current_user)


