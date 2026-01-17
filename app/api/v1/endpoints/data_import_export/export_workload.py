# -*- coding: utf-8 -*-
"""
负荷数据导出 routes
"""

import io
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.pmo import PmoResourceAllocation
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.data_import_export import ExportWorkloadRequest

router = APIRouter()


@router.post("/export/workload", response_class=StreamingResponse)
def export_workload(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ExportWorkloadRequest,
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    导出负荷数据（Excel）
    基于资源分配和工时数据计算人员负荷
    """
    try:
        import openpyxl
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    users = db.query(User).filter(User.is_active == True).all()

    data = []
    for user in users:
        timesheets = (
            db.query(Timesheet)
            .filter(
                and_(
                    Timesheet.user_id == user.id,
                    Timesheet.work_date >= export_in.start_date,
                    Timesheet.work_date <= export_in.end_date,
                    Timesheet.status == "APPROVED",
                )
            )
            .all()
        )

        total_hours = sum(float(ts.hours or 0) for ts in timesheets)

        work_days = 0
        current_date = export_in.start_date
        while current_date <= export_in.end_date:
            if current_date.weekday() < 5:
                work_days += 1
            current_date += timedelta(days=1)

        avg_daily_hours = total_hours / work_days if work_days > 0 else 0
        standard_hours = work_days * 8
        utilization_rate = (
            (total_hours / standard_hours * 100) if standard_hours > 0 else 0
        )

        allocations = (
            db.query(PmoResourceAllocation)
            .filter(
                and_(
                    PmoResourceAllocation.resource_id == user.id,
                    PmoResourceAllocation.status.in_(["PLANNED", "ACTIVE"]),
                )
            )
            .all()
        )

        project_count = len(set([a.project_id for a in allocations if a.project_id]))

        department_name = user.department if hasattr(user, "department") else ""

        data.append(
            {
                "人员姓名": user.real_name or user.username,
                "用户名": user.username,
                "部门": department_name,
                "总工时(小时)": round(total_hours, 2),
                "工作日数": work_days,
                "平均每日工时": round(avg_daily_hours, 2),
                "标准工时(小时)": standard_hours,
                "利用率(%)": round(utilization_rate, 2),
                "分配项目数": project_count,
                "负荷状态": "超负荷"
                if utilization_rate > 100
                else ("正常" if utilization_rate > 80 else "空闲"),
            }
        )

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="负荷数据", index=False)

        worksheet = writer.sheets["负荷数据"]
        column_widths = {
            "A": 12,
            "B": 15,
            "C": 15,
            "D": 12,
            "E": 10,
            "F": 12,
            "G": 12,
            "H": 12,
            "I": 12,
            "J": 12,
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

    filename = f"负荷数据_{export_in.start_date.strftime('%Y%m%d')}_{export_in.end_date.strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
