# -*- coding: utf-8 -*-
"""
项目数据导出 routes
"""

import io
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.data_import_export import (
    ExportProjectDetailRequest,
    ExportProjectListRequest,
)
from app.services.data_scope_service import DataScopeService

router = APIRouter()


@router.post("/export/project_list", response_class=StreamingResponse)
def export_project_list(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ExportProjectListRequest,
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    导出项目列表（Excel）
    """
    try:
        import openpyxl
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    query = db.query(Project).filter(Project.is_active == True)

    filters = export_in.filters or {}
    if filters.get("keyword"):
        keyword = filters["keyword"]
        query = query.filter(
            or_(
                Project.project_name.contains(keyword),
                Project.project_code.contains(keyword),
                Project.contract_no.contains(keyword),
            )
        )
    if filters.get("customer_id"):
        query = query.filter(Project.customer_id == filters["customer_id"])
    if filters.get("stage"):
        query = query.filter(Project.stage == filters["stage"])
    if filters.get("status"):
        query = query.filter(Project.status == filters["status"])
    if filters.get("health"):
        query = query.filter(Project.health == filters["health"])
    if filters.get("pm_id"):
        query = query.filter(Project.pm_id == filters["pm_id"])
    if filters.get("project_type"):
        query = query.filter(Project.project_type == filters["project_type"])

    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    projects = query.order_by(desc(Project.created_at)).all()

    stage_names = {
        "S1": "需求进入",
        "S2": "方案设计",
        "S3": "采购备料",
        "S4": "加工制造",
        "S5": "装配调试",
        "S6": "出厂验收(FAT)",
        "S7": "包装发运",
        "S8": "现场安装(SAT)",
        "S9": "质保结项",
    }

    health_names = {
        "H1": "正常(绿色)",
        "H2": "有风险(黄色)",
        "H3": "阻塞(红色)",
        "H4": "已完结(灰色)",
    }

    data = []
    for project in projects:
        data.append(
            {
                "项目编码": project.project_code or "",
                "项目名称": project.project_name or "",
                "客户名称": project.customer_name or "",
                "合同编号": project.contract_no or "",
                "合同金额": float(project.contract_amount or 0),
                "项目经理": project.pm_name or "",
                "项目类型": project.project_type or "",
                "阶段": project.stage or "",
                "阶段名称": stage_names.get(project.stage, project.stage or ""),
                "状态": project.status or "",
                "健康度": project.health or "",
                "健康度名称": health_names.get(project.health, project.health or "")
                if project.health
                else "",
                "进度(%)": float(project.progress_pct or 0),
                "计划开始日期": project.planned_start_date.strftime("%Y-%m-%d")
                if project.planned_start_date
                else "",
                "计划结束日期": project.planned_end_date.strftime("%Y-%m-%d")
                if project.planned_end_date
                else "",
                "实际开始日期": project.actual_start_date.strftime("%Y-%m-%d")
                if project.actual_start_date
                else "",
                "实际结束日期": project.actual_end_date.strftime("%Y-%m-%d")
                if project.actual_end_date
                else "",
                "创建时间": project.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if project.created_at
                else "",
                "更新时间": project.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                if project.updated_at
                else "",
            }
        )

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="项目列表", index=False)

        worksheet = writer.sheets["项目列表"]
        column_widths = {
            "A": 15,
            "B": 30,
            "C": 20,
            "D": 15,
            "E": 12,
            "F": 12,
            "G": 12,
            "H": 8,
            "I": 15,
            "J": 10,
            "K": 8,
            "L": 15,
            "M": 10,
            "N": 12,
            "O": 12,
            "P": 12,
            "Q": 12,
            "R": 18,
            "S": 18,
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

    filename = f"项目列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.post(
    "/export/project_detail", response_model=Any, status_code=status.HTTP_200_OK
)
def export_project_detail(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ExportProjectDetailRequest,
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    导出项目详情（含任务/成本）
    """
    from app.services.project_export_service import create_project_detail_excel
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, export_in.project_id)

    try:
        output = create_project_detail_excel(
            db, project, export_in.include_tasks, export_in.include_costs
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="Excel处理库未安装，请安装openpyxl")

    filename = f"项目详情_{project.project_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
