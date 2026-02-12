# -*- coding: utf-8 -*-
"""
工时数据导出 routes
"""

import io
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.data_import_export import ExportTimesheetRequest
from app.services.import_export_engine import ExcelExportEngine

router = APIRouter()


@router.post("/export/timesheet", response_class=StreamingResponse)
def export_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    export_in: ExportTimesheetRequest,
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    导出工时数据（按日期范围，Excel）
    """
    query = db.query(Timesheet).filter(
        and_(
            Timesheet.work_date >= export_in.start_date,
            Timesheet.work_date <= export_in.end_date,
        )
    )

    filters = export_in.filters or {}
    if filters.get("user_id"):
        query = query.filter(Timesheet.user_id == filters["user_id"])
    if filters.get("project_id"):
        query = query.filter(Timesheet.project_id == filters["project_id"])
    if filters.get("department_id"):
        query = query.filter(Timesheet.department_id == filters["department_id"])
    if filters.get("status"):
        query = query.filter(Timesheet.status == filters["status"])

    timesheets = query.order_by(Timesheet.work_date, Timesheet.user_id).all()

    status_names = {
        "DRAFT": "草稿",
        "SUBMITTED": "已提交",
        "APPROVED": "已通过",
        "REJECTED": "已驳回",
        "CANCELLED": "已取消",
    }

    overtime_type_names = {
        "NORMAL": "正常工时",
        "OVERTIME": "加班",
        "WEEKEND": "周末加班",
        "HOLIDAY": "节假日加班",
    }

    data = []
    for ts in timesheets:
        data.append(
            {
                "工作日期": ts.work_date.strftime("%Y-%m-%d") if ts.work_date else "",
                "人员姓名": ts.user_name or "",
                "部门": ts.department_name or "",
                "项目编码": ts.project_code or "",
                "项目名称": ts.project_name or "",
                "任务名称": ts.task_name or "",
                "工时(小时)": float(ts.hours or 0),
                "加班类型": ts.overtime_type or "",
                "加班类型名称": overtime_type_names.get(
                    ts.overtime_type, ts.overtime_type or ""
                ),
                "工作内容": ts.work_content or "",
                "工作成果": ts.work_result or "",
                "更新前进度(%)": ts.progress_before or 0,
                "更新后进度(%)": ts.progress_after or 0,
                "状态": ts.status or "",
                "状态名称": status_names.get(ts.status, ts.status or ""),
                "提交时间": ts.submit_time.strftime("%Y-%m-%d %H:%M:%S")
                if ts.submit_time
                else "",
                "审核人": ts.approver_name or "",
                "审核时间": ts.approve_time.strftime("%Y-%m-%d %H:%M:%S")
                if ts.approve_time
                else "",
                "审核意见": ts.approve_comment or "",
            }
        )

    labels = [
        "工作日期",
        "人员姓名",
        "部门",
        "项目编码",
        "项目名称",
        "任务名称",
        "工时(小时)",
        "加班类型",
        "加班类型名称",
        "工作内容",
        "工作成果",
        "更新前进度(%)",
        "更新后进度(%)",
        "状态",
        "状态名称",
        "提交时间",
        "审核人",
        "审核时间",
        "审核意见",
    ]
    widths = [
        12,
        12,
        15,
        15,
        30,
        30,
        12,
        12,
        15,
        40,
        40,
        12,
        12,
        12,
        12,
        18,
        12,
        18,
        40,
    ]
    columns = ExcelExportEngine.build_columns(labels, widths=widths)
    output = ExcelExportEngine.export_table(
        data=data,
        columns=columns,
        sheet_name="工时数据",
        title=None,
    )

    filename = f"工时数据_{export_in.start_date.strftime('%Y%m%d')}_{export_in.end_date.strftime('%Y%m%d')}.xlsx"

    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
