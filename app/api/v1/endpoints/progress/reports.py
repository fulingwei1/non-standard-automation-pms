# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 进度填报
包含：进度报告CRUD、进度报告统计
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.progress import ProgressReport, Task
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.progress import (
    ProgressReportCreate,
    ProgressReportListResponse,
    ProgressReportResponse,
    ProgressReportUpdate,
)

router = APIRouter()


# ==================== 进度填报 ====================

@router.post("/progress-reports", response_model=ProgressReportResponse, status_code=status.HTTP_201_CREATED)
def create_progress_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: ProgressReportCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交进度报告（日报/周报）
    """
    # 验证至少指定一个关联对象
    if not report_in.project_id and not report_in.machine_id and not report_in.task_id:
        raise HTTPException(status_code=400, detail="必须指定项目ID、机台ID或任务ID中的至少一个")

    # 验证项目是否存在
    if report_in.project_id:
        project = db.query(Project).filter(Project.id == report_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

    # 验证机台是否存在
    if report_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == report_in.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")
        # 如果同时指定了项目ID，验证机台属于该项目
        if report_in.project_id and machine.project_id != report_in.project_id:
            raise HTTPException(status_code=400, detail="机台不属于指定的项目")

    # 验证任务是否存在
    if report_in.task_id:
        task = db.query(Task).filter(Task.id == report_in.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        # 如果同时指定了项目ID，验证任务属于该项目
        if report_in.project_id and task.project_id != report_in.project_id:
            raise HTTPException(status_code=400, detail="任务不属于指定的项目")
        # 如果同时指定了机台ID，验证任务属于该机台
        if report_in.machine_id and task.machine_id != report_in.machine_id:
            raise HTTPException(status_code=400, detail="任务不属于指定的机台")

    # 创建进度报告
    progress_report = ProgressReport(
        report_type=report_in.report_type,
        report_date=report_in.report_date,
        project_id=report_in.project_id,
        machine_id=report_in.machine_id,
        task_id=report_in.task_id,
        content=report_in.content,
        completed_work=report_in.completed_work,
        planned_work=report_in.planned_work,
        issues=report_in.issues,
        next_plan=report_in.next_plan,
        created_by=current_user.id
    )

    db.add(progress_report)
    db.commit()
    db.refresh(progress_report)

    return progress_report


@router.get("/progress-reports", response_model=ProgressReportListResponse, status_code=status.HTTP_200_OK)
def read_progress_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    report_type: Optional[str] = Query(None, description="报告类型筛选（daily/weekly）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取进度报告列表
    """
    query = db.query(ProgressReport)

    # 项目筛选
    if project_id:
        query = query.filter(ProgressReport.project_id == project_id)

    # 机台筛选
    if machine_id:
        query = query.filter(ProgressReport.machine_id == machine_id)

    # 任务筛选
    if task_id:
        query = query.filter(ProgressReport.task_id == task_id)

    # 报告类型筛选
    if report_type:
        query = query.filter(ProgressReport.report_type == report_type)

    # 日期范围筛选
    if start_date:
        query = query.filter(ProgressReport.report_date >= start_date)
    if end_date:
        query = query.filter(ProgressReport.report_date <= end_date)

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    reports = query.order_by(ProgressReport.report_date.desc(), ProgressReport.created_at.desc()).offset(offset).limit(page_size).all()

    return ProgressReportListResponse(
        items=reports,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/progress-reports/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_progress_report_statistics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取进度报告统计信息
    """
    query = db.query(ProgressReport)

    # 筛选条件
    if project_id:
        query = query.filter(ProgressReport.project_id == project_id)
    if machine_id:
        query = query.filter(ProgressReport.machine_id == machine_id)
    if start_date:
        query = query.filter(ProgressReport.report_date >= start_date)
    if end_date:
        query = query.filter(ProgressReport.report_date <= end_date)

    reports = query.all()

    # 统计
    total_reports = len(reports)
    daily_reports = len([r for r in reports if r.report_type == "daily"])
    weekly_reports = len([r for r in reports if r.report_type == "weekly"])

    # 按创建人统计
    creator_stats = {}
    for report in reports:
        creator_id = report.created_by
        if creator_id not in creator_stats:
            creator = db.query(User).filter(User.id == creator_id).first()
            creator_stats[creator_id] = {
                "user_id": creator_id,
                "user_name": creator.real_name or creator.username if creator else "未知",
                "count": 0
            }
        creator_stats[creator_id]["count"] += 1

    # 按日期统计（最近30天）
    today = date.today()
    date_stats = {}
    for i in range(30):
        check_date = today - timedelta(days=i)
        date_stats[check_date.isoformat()] = len([
            r for r in reports
            if r.report_date == check_date
        ])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_reports": total_reports,
            "daily_reports": daily_reports,
            "weekly_reports": weekly_reports,
            "by_creator": list(creator_stats.values()),
            "by_date": date_stats,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
    )


@router.get("/progress-reports/{report_id}", response_model=ProgressReportResponse, status_code=status.HTTP_200_OK)
def read_progress_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取进度报告详情
    """
    progress_report = db.query(ProgressReport).filter(ProgressReport.id == report_id).first()
    if not progress_report:
        raise HTTPException(status_code=404, detail="进度报告不存在")

    return progress_report


@router.put("/progress-reports/{report_id}", response_model=ProgressReportResponse, status_code=status.HTTP_200_OK)
def update_progress_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    report_in: ProgressReportUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新进度报告
    """
    progress_report = db.query(ProgressReport).filter(ProgressReport.id == report_id).first()
    if not progress_report:
        raise HTTPException(status_code=404, detail="进度报告不存在")

    # 权限检查：只能更新自己创建的报告（或管理员）
    if progress_report.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权更新此进度报告")

    update_data = report_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(progress_report, field, value)

    db.add(progress_report)
    db.commit()
    db.refresh(progress_report)

    return progress_report


@router.delete("/progress-reports/{report_id}", status_code=status.HTTP_200_OK)
def delete_progress_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除进度报告
    """
    progress_report = db.query(ProgressReport).filter(ProgressReport.id == report_id).first()
    if not progress_report:
        raise HTTPException(status_code=404, detail="进度报告不存在")

    # 权限检查：只能删除自己创建的报告（或管理员）
    if progress_report.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除此进度报告")

    db.delete(progress_report)
    db.commit()

    return {"message": "进度报告已删除", "id": report_id}
