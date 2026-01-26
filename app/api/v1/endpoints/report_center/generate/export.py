# -*- coding: utf-8 -*-
"""
报表生成 - 导出功能
"""
import os
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Project
from app.models.report_center import ReportGeneration
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.report_center import ReportExportRequest

router = APIRouter()


@router.post("/export", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def export_report(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ReportExportRequest,
    current_user: User = Depends(security.require_permission("report:export")),
) -> Any:
    """
    导出报表（xlsx/pdf/csv）
    """
    from app.services.report_export_service import report_export_service

    generation = db.query(ReportGeneration).filter(ReportGeneration.id == export_in.report_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="报表不存在")

    # 准备导出数据
    report_data = generation.report_data or {}
    report_title = generation.report_title or f"{generation.report_type}报表"
    filename = f"report_{generation.id}"

    try:
        export_format = export_in.export_format.upper()

        if export_format == 'XLSX':
            filepath = report_export_service.export_to_excel(
                data=report_data,
                filename=filename,
                title=report_title
            )
        elif export_format == 'PDF':
            filepath = report_export_service.export_to_pdf(
                data=report_data,
                filename=filename,
                title=report_title
            )
        elif export_format == 'CSV':
            filepath = report_export_service.export_to_csv(
                data=report_data,
                filename=filename
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {export_format}")

        # 更新导出记录
        generation.export_format = export_format
        generation.export_path = filepath
        generation.exported_at = datetime.now()
        db.add(generation)
        db.commit()

        # 返回下载链接
        return ResponseModel(
            code=200,
            message="导出成功",
            data={
                "report_id": generation.id,
                "format": export_format,
                "file_path": filepath,
                "download_url": f"/api/v1/reports/download/{generation.id}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/export-direct", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def export_direct(
    *,
    db: Session = Depends(deps.get_db),
    report_type: str = Query(..., description="报表类型"),
    export_format: str = Query("xlsx", description="导出格式: xlsx/pdf/csv"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    直接导出报表（不需要先生成报表记录）
    """
    from app.services.report_export_service import (
        ReportGenerator,
        report_export_service,
    )

    # 根据报表类型生成数据
    report_data = {}
    report_title = ""

    if report_type == 'PROJECT_LIST':
        # 项目列表报表
        query = db.query(Project)
        if project_id:
            query = query.filter(Project.id == project_id)
        projects = query.all()

        project_list = []
        for p in projects:
            project_list.append({
                "项目编码": p.project_code,
                "项目名称": p.project_name,
                "客户": p.customer_name if hasattr(p, 'customer_name') else '',
                "阶段": p.stage,
                "健康度": p.health,
                "状态": p.status,
                "计划开始": str(p.planned_start_date) if p.planned_start_date else '',
                "计划结束": str(p.planned_end_date) if p.planned_end_date else '',
            })

        report_data = ReportGenerator.generate_project_report(project_list)
        report_title = "项目列表报表"

    elif report_type == 'HEALTH_DISTRIBUTION':
        # 健康度分布报表
        health_stats = db.query(
            Project.health,
            func.count(Project.id).label('count')
        ).filter(Project.status != "CANCELLED").group_by(Project.health).all()

        health_list = []
        for stat in health_stats:
            health_list.append({
                "健康度": stat.health or "H4",
                "项目数量": stat.count
            })

        report_data = {"details": health_list}
        report_title = "项目健康度分布报表"

    elif report_type == 'UTILIZATION':
        # 人员利用率报表
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        timesheets = db.query(Timesheet).filter(
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status == "APPROVED"
        ).all()

        user_hours = {}
        for ts in timesheets:
            if ts.user_id not in user_hours:
                user_hours[ts.user_id] = 0
            user_hours[ts.user_id] += float(ts.hours or 0)

        work_days = sum(1 for d in range((end_date - start_date).days + 1)
                       if (start_date + timedelta(days=d)).weekday() < 5)
        standard_hours = work_days * 8

        util_list = []
        for user_id, hours in user_hours.items():
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                rate = (hours / standard_hours * 100) if standard_hours > 0 else 0
                util_list.append({
                    "姓名": user.real_name or user.username,
                    "部门": user.department or '',
                    "工时(小时)": round(hours, 1),
                    "标准工时": standard_hours,
                    "利用率": f"{rate:.1f}%"
                })

        report_data = ReportGenerator.generate_utilization_report(util_list)
        report_title = f"人员利用率报表 ({start_date} ~ {end_date})"

    else:
        raise HTTPException(status_code=400, detail=f"不支持的报表类型: {report_type}")

    # 导出文件
    try:
        filename = f"{report_type.lower()}_{datetime.now().strftime('%Y%m%d')}"
        export_fmt = export_format.upper()

        if export_fmt == 'XLSX':
            filepath = report_export_service.export_to_excel(report_data, filename, report_title)
        elif export_fmt == 'PDF':
            filepath = report_export_service.export_to_pdf(report_data, filename, report_title)
        elif export_fmt == 'CSV':
            filepath = report_export_service.export_to_csv(report_data, filename)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {export_format}")

        return ResponseModel(
            code=200,
            message="导出成功",
            data={
                "file_path": filepath,
                "report_type": report_type,
                "format": export_fmt
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
