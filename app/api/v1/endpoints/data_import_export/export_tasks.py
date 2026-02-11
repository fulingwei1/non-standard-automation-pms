# -*- coding: utf-8 -*-
"""
任务数据导出 routes
"""

import io
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.progress import Task
from app.models.project import Project
from app.models.user import User
from app.schemas.data_import_export import ExportTaskListRequest
from app.services.data_scope import DataScopeService

router = APIRouter()


@router.post("/export/task_list", response_class=StreamingResponse)
def export_task_list(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ExportTaskListRequest,
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    导出任务列表（Excel）
    """
    try:
        import openpyxl
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    query = db.query(Task)

    filters = export_in.filters or {}
    if filters.get("project_id"):
        query = query.filter(Task.project_id == filters["project_id"])
    if filters.get("machine_id"):
        query = query.filter(Task.machine_id == filters["machine_id"])
    if filters.get("stage"):
        query = query.filter(Task.stage == filters["stage"])
    if filters.get("status"):
        query = query.filter(Task.status == filters["status"])
    if filters.get("owner_id"):
        query = query.filter(Task.owner_id == filters["owner_id"])
    query = apply_keyword_filter(query, Task, filters.get("keyword"), "task_name")

    scoped_project_query = db.query(Project.id)
    if filters.get("project_id"):
        scoped_project_query = scoped_project_query.filter(
            Project.id == filters["project_id"]
        )
    scoped_project_query = DataScopeService.filter_projects_by_scope(
        db, scoped_project_query, current_user
    )
    allowed_projects_subquery = scoped_project_query.subquery()
    query = query.filter(Task.project_id.in_(allowed_projects_subquery))

    tasks = query.order_by(desc(Task.created_at)).all()

    status_names = {
        "TODO": "待办",
        "IN_PROGRESS": "进行中",
        "BLOCKED": "阻塞",
        "DONE": "已完成",
        "CANCELLED": "已取消",
    }

    data = []
    for task in tasks:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        owner = (
            db.query(User).filter(User.id == task.owner_id).first()
            if task.owner_id
            else None
        )

        data.append(
            {
                "任务ID": task.id,
                "任务名称": task.task_name or "",
                "项目编码": project.project_code if project else "",
                "项目名称": project.project_name if project else "",
                "阶段": task.stage or "",
                "状态": task.status or "",
                "状态名称": status_names.get(task.status, task.status or ""),
                "负责人": owner.real_name or owner.username if owner else "",
                "计划开始日期": task.plan_start.strftime("%Y-%m-%d")
                if task.plan_start
                else "",
                "计划结束日期": task.plan_end.strftime("%Y-%m-%d")
                if task.plan_end
                else "",
                "实际开始日期": task.actual_start.strftime("%Y-%m-%d")
                if task.actual_start
                else "",
                "实际结束日期": task.actual_end.strftime("%Y-%m-%d")
                if task.actual_end
                else "",
                "进度(%)": task.progress_percent or 0,
                "权重": float(task.weight or 0),
                "阻塞原因": task.block_reason or "",
                "创建时间": task.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if task.created_at
                else "",
                "更新时间": task.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                if task.updated_at
                else "",
            }
        )

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="任务列表", index=False)

        worksheet = writer.sheets["任务列表"]
        column_widths = {
            "A": 10,
            "B": 30,
            "C": 15,
            "D": 30,
            "E": 8,
            "F": 12,
            "G": 12,
            "H": 12,
            "I": 12,
            "J": 12,
            "K": 12,
            "L": 12,
            "M": 10,
            "N": 8,
            "O": 40,
            "P": 18,
            "Q": 18,
        }
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

        from openpyxl.styles import Alignment, Font, PatternFill

        header_fill = PatternFill(
            start_color="366092", end_color="366092", fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

    output.seek(0)

    filename = f"任务列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
