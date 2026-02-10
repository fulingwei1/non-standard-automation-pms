# -*- coding: utf-8 -*-
"""
工时统一报表端点

提供统一的工时报表查询接口，整合多种报表格式
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


def _build_base_filter(start_date: date, end_date: date, department_id, project_id, user_id):
    """构建基础过滤条件"""
    filters = [
        Timesheet.work_date >= start_date,
        Timesheet.work_date <= end_date,
        Timesheet.status == "APPROVED",
    ]
    if department_id:
        filters.append(Timesheet.department_id == department_id)
    if project_id:
        filters.append(Timesheet.project_id == project_id)
    if user_id:
        filters.append(Timesheet.user_id == user_id)
    return filters


def _report_summary(db: Session, filters):
    """汇总报表"""
    result = db.query(
        func.coalesce(func.sum(Timesheet.hours), 0).label("total_hours"),
        func.count(func.distinct(Timesheet.user_id)).label("total_users"),
        func.count(Timesheet.id).label("total_records"),
        func.count(func.distinct(Timesheet.project_id)).label("total_projects"),
    ).filter(*filters).first()

    return {
        "total_hours": float(result.total_hours) if result else 0,
        "total_users": result.total_users if result else 0,
        "total_records": result.total_records if result else 0,
        "total_projects": result.total_projects if result else 0,
    }


def _report_detail(db: Session, filters):
    """明细报表"""
    records = db.query(Timesheet).filter(*filters).order_by(
        Timesheet.work_date.desc(), Timesheet.user_id
    ).all()

    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_name": r.user_name,
            "project_id": r.project_id,
            "project_name": r.project_name,
            "work_date": r.work_date.isoformat() if r.work_date else None,
            "hours": float(r.hours) if r.hours else 0,
            "overtime_type": r.overtime_type,
            "work_content": r.work_content,
        }
        for r in records
    ]


def _report_by_project(db: Session, filters):
    """按项目汇总"""
    rows = db.query(
        Timesheet.project_id,
        Timesheet.project_name,
        func.coalesce(func.sum(Timesheet.hours), 0).label("hours"),
        func.count(func.distinct(Timesheet.user_id)).label("users"),
        func.count(Timesheet.id).label("records"),
    ).filter(*filters).group_by(
        Timesheet.project_id, Timesheet.project_name
    ).order_by(func.sum(Timesheet.hours).desc()).all()

    return [
        {
            "project_id": row.project_id,
            "project_name": row.project_name,
            "hours": float(row.hours),
            "users": row.users,
            "records": row.records,
        }
        for row in rows
    ]


def _report_by_user(db: Session, filters):
    """按用户汇总"""
    rows = db.query(
        Timesheet.user_id,
        Timesheet.user_name,
        Timesheet.department_name,
        func.coalesce(func.sum(Timesheet.hours), 0).label("hours"),
        func.count(func.distinct(Timesheet.project_id)).label("projects"),
        func.count(Timesheet.id).label("records"),
    ).filter(*filters).group_by(
        Timesheet.user_id, Timesheet.user_name, Timesheet.department_name
    ).order_by(func.sum(Timesheet.hours).desc()).all()

    return [
        {
            "user_id": row.user_id,
            "user_name": row.user_name,
            "department_name": row.department_name,
            "hours": float(row.hours),
            "projects": row.projects,
            "records": row.records,
        }
        for row in rows
    ]


_REPORT_BUILDERS = {
    "summary": _report_summary,
    "detail": _report_detail,
    "by_project": _report_by_project,
    "by_user": _report_by_user,
}


@router.get("/reports-unified", response_model=ResponseModel)
def get_unified_timesheet_report(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    report_type: str = Query("summary", description="报表类型: summary, detail, by_project, by_user"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取统一格式的工时报表

    支持多种报表类型：
    - summary: 汇总报表
    - detail: 明细报表
    - by_project: 按项目汇总
    - by_user: 按用户汇总
    """
    filters = _build_base_filter(start_date, end_date, department_id, project_id, user_id)

    builder = _REPORT_BUILDERS.get(report_type, _report_summary)
    data = builder(db, filters)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "report_type": report_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": data,
        },
    )


@router.get("/reports-unified/export", response_model=ResponseModel)
def export_unified_timesheet_report(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    report_type: str = Query("summary", description="报表类型"),
    format: str = Query("excel", description="导出格式: excel, pdf"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    导出统一格式的工时报表

    注意：完整的文件导出（Excel/PDF 生成）需要配合前端实现，
    此端点返回报表数据供前端生成文件。
    """
    filters = _build_base_filter(start_date, end_date, None, None, None)
    builder = _REPORT_BUILDERS.get(report_type, _report_summary)
    data = builder(db, filters)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "report_type": report_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "format": format,
            "data": data,
        },
    )
