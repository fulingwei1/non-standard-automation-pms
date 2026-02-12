# -*- coding: utf-8 -*-
"""
生产管理模块 - 报工管理端点

包含：开工报告、进度上报、完工报告、审批、我的报工
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.production import Worker, WorkOrder, WorkReport, Workstation
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.production import (
    WorkReportCompleteRequest,
    WorkReportProgressRequest,
    WorkReportResponse,
    WorkReportStartRequest,
)

from .utils import generate_report_no
from app.common.query_filters import apply_pagination

router = APIRouter()


def _get_work_report_response(db: Session, report: WorkReport) -> WorkReportResponse:
    """构建报工响应对象的辅助函数"""
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()
    worker = db.query(Worker).filter(Worker.id == report.worker_id).first()

    return WorkReportResponse(
        id=report.id,
        report_no=report.report_no,
        work_order_id=report.work_order_id,
        work_order_no=work_order.work_order_no if work_order else None,
        worker_id=report.worker_id,
        worker_name=worker.worker_name if worker else None,
        report_type=report.report_type,
        report_time=report.report_time,
        progress_percent=report.progress_percent,
        work_hours=float(report.work_hours) if report.work_hours else None,
        completed_qty=report.completed_qty,
        qualified_qty=report.qualified_qty,
        defect_qty=report.defect_qty,
        status=report.status,
        report_note=report.report_note,
        approved_by=report.approved_by,
        approved_at=report.approved_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


# ==================== 报工系统 ====================

@router.post("/work-reports/start", response_model=WorkReportResponse)
def start_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开工报告（扫码开工）
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if work_order.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail="只有已派工的工单才能开工")

    # 获取当前工人（从用户关联）
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")

    # 生成报工单号
    report_no = generate_report_no(db)

    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=worker.id,
        report_type="START",
        report_time=datetime.now(),
        status="PENDING",
        report_note=report_in.report_note,
    )
    db.add(report)

    # 更新工单状态
    work_order.status = "STARTED"
    work_order.actual_start_time = datetime.now()
    work_order.progress = 0

    # 更新工位状态
    if work_order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == work_order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = work_order.id
            workstation.current_worker_id = worker.id
            db.add(workstation)

    db.commit()
    db.refresh(report)

    return _get_work_report_response(db, report)


@router.post("/work-reports/progress", response_model=WorkReportResponse)
def progress_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportProgressRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    进度上报
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if work_order.status not in ["STARTED", "PAUSED"]:
        raise HTTPException(status_code=400, detail="只有已开始或已暂停的工单才能上报进度")

    # 获取当前工人
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")

    # 生成报工单号
    report_no = generate_report_no(db)

    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=worker.id,
        report_type="PROGRESS",
        report_time=datetime.now(),
        progress_percent=report_in.progress_percent,
        work_hours=report_in.work_hours,
        status="PENDING",
        report_note=report_in.report_note,
    )
    db.add(report)

    # 更新工单进度
    work_order.progress = report_in.progress_percent
    if report_in.work_hours:
        work_order.actual_hours = (work_order.actual_hours or 0) + report_in.work_hours

    db.commit()
    db.refresh(report)

    return _get_work_report_response(db, report)


@router.post("/work-reports/complete", response_model=WorkReportResponse)
def complete_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: WorkReportCompleteRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完工报告（数量/合格数）
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == report_in.work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if work_order.status not in ["STARTED", "PAUSED"]:
        raise HTTPException(status_code=400, detail="只有已开始或已暂停的工单才能完工")

    # 检查完成数量
    if report_in.completed_qty > work_order.plan_qty:
        raise HTTPException(status_code=400, detail="完成数量不能超过计划数量")

    if report_in.qualified_qty > report_in.completed_qty:
        raise HTTPException(status_code=400, detail="合格数量不能超过完成数量")

    # 获取当前工人
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")

    # 生成报工单号
    report_no = generate_report_no(db)

    report = WorkReport(
        report_no=report_no,
        work_order_id=report_in.work_order_id,
        worker_id=worker.id,
        report_type="COMPLETE",
        report_time=datetime.now(),
        completed_qty=report_in.completed_qty,
        qualified_qty=report_in.qualified_qty,
        defect_qty=report_in.defect_qty or 0,
        work_hours=report_in.work_hours,
        status="PENDING",
        report_note=report_in.report_note,
    )
    db.add(report)

    # 更新工单
    work_order.completed_qty = report_in.completed_qty
    work_order.qualified_qty = report_in.qualified_qty
    work_order.defect_qty = report_in.defect_qty or 0
    work_order.progress = 100

    if report_in.work_hours:
        work_order.actual_hours = (work_order.actual_hours or 0) + report_in.work_hours

    # 如果完成数量达到计划数量，自动完成工单
    if report_in.completed_qty >= work_order.plan_qty:
        work_order.status = "COMPLETED"
        work_order.actual_end_time = datetime.now()

        # 更新工位状态
        if work_order.workstation_id:
            workstation = db.query(Workstation).filter(Workstation.id == work_order.workstation_id).first()
            if workstation:
                workstation.status = "IDLE"
                workstation.current_work_order_id = None
                workstation.current_worker_id = None
                db.add(workstation)

    db.commit()
    db.refresh(report)

    return _get_work_report_response(db, report)


@router.get("/work-reports/{report_id}", response_model=WorkReportResponse)
def get_work_report_detail(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报工详情
    """
    report = db.query(WorkReport).filter(WorkReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报工记录不存在")

    return _get_work_report_response(db, report)


@router.get("/work-reports", response_model=PaginatedResponse)
def read_work_reports(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    work_order_id: Optional[int] = Query(None, description="工单ID筛选"),
    worker_id: Optional[int] = Query(None, description="工人ID筛选"),
    report_type: Optional[str] = Query(None, description="报工类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报工记录列表
    """
    query = db.query(WorkReport)

    if work_order_id:
        query = query.filter(WorkReport.work_order_id == work_order_id)

    if worker_id:
        query = query.filter(WorkReport.worker_id == worker_id)

    if report_type:
        query = query.filter(WorkReport.report_type == report_type)

    if status:
        query = query.filter(WorkReport.status == status)

    total = query.count()
    reports = apply_pagination(query.order_by(desc(WorkReport.report_time)), pagination.offset, pagination.limit).all()

    items = [_get_work_report_response(db, report) for report in reports]

    return pagination.to_response(items, total)


@router.put("/work-reports/{report_id}/approve", response_model=ResponseModel)
def approve_work_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    approved: bool = Query(True, description="是否审批通过"),
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报工审批（车间主管）
    """
    report = db.query(WorkReport).filter(WorkReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报工记录不存在")

    if report.status != "PENDING":
        raise HTTPException(status_code=400, detail="只有待审核的报工记录才能审批")

    if approved:
        report.status = "APPROVED"
        report.approved_by = current_user.id
        report.approved_at = datetime.now()
    else:
        report.status = "REJECTED"
        report.approved_by = current_user.id
        report.approved_at = datetime.now()

    if approval_note:
        report.report_note = (report.report_note or "") + f"\n审批意见：{approval_note}"

    db.add(report)
    db.commit()

    return ResponseModel(
        code=200,
        message="审批成功" if approved else "已驳回"
    )


@router.get("/work-reports/my", response_model=PaginatedResponse)
def get_my_work_reports(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    我的报工记录（工人查看）
    """
    # 获取当前工人
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=400, detail="当前用户未关联工人信息")

    query = db.query(WorkReport).filter(WorkReport.worker_id == worker.id)

    total = query.count()
    reports = apply_pagination(query.order_by(desc(WorkReport.report_time)), pagination.offset, pagination.limit).all()

    items = []
    for report in reports:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == report.work_order_id).first()

        items.append(WorkReportResponse(
            id=report.id,
            report_no=report.report_no,
            work_order_id=report.work_order_id,
            work_order_no=work_order.work_order_no if work_order else None,
            worker_id=report.worker_id,
            worker_name=worker.worker_name,
            report_type=report.report_type,
            report_time=report.report_time,
            progress_percent=report.progress_percent,
            work_hours=float(report.work_hours) if report.work_hours else None,
            completed_qty=report.completed_qty,
            qualified_qty=report.qualified_qty,
            defect_qty=report.defect_qty,
            status=report.status,
            report_note=report.report_note,
            approved_by=report.approved_by,
            approved_at=report.approved_at,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))

    return pagination.to_response(items, total)
