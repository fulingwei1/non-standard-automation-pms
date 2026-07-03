# -*- coding: utf-8 -*-
"""工时数据同步端点."""

from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range_by_ym
from app.core import security
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.timesheet.timesheet_sync_service import TimesheetSyncService

router = APIRouter()

SYNC_TARGETS = {"all", "finance", "rd", "project", "hr"}


def _sorted_ids(values: List[Optional[int]]) -> List[int]:
    return sorted({int(value) for value in values if value})


def _empty_summary(year: int, month: int, sync_target: str) -> Dict[str, Any]:
    return {
        "year": year,
        "month": month,
        "sync_target": sync_target,
        "approved_timesheets": 0,
        "project_ids": [],
        "rd_project_ids": [],
        "results": {},
        "failed_count": 0,
        "errors": [],
    }


@router.post("/sync", response_model=ResponseModel)
def sync_timesheet(
    year: int = Query(..., ge=2000, le=2100, description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    sync_target: str = Query("all", description="同步目标: all/finance/rd/project/hr"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """同步已审批工时到财务、项目、研发或 HR 统计链路."""
    target = (sync_target or "all").lower()
    if target not in SYNC_TARGETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的同步目标: {sync_target}",
        )

    month_start, month_end = get_month_range_by_ym(year, month)
    filters = [
        Timesheet.status == "APPROVED",
        Timesheet.work_date >= month_start,
        Timesheet.work_date <= month_end,
    ]
    if project_id:
        filters.append(Timesheet.project_id == project_id)

    timesheets = db.query(Timesheet).filter(*filters).all()
    if not timesheets:
        data = _empty_summary(year, month, target)
        return ResponseModel(code=200, message="没有已审批工时需要同步", data=data)

    service = TimesheetSyncService(db)
    project_ids = _sorted_ids([ts.project_id for ts in timesheets])
    rd_project_ids = _sorted_ids([ts.rd_project_id for ts in timesheets])
    requested_targets = ["finance", "rd", "project", "hr"] if target == "all" else [target]
    results: Dict[str, List[Dict[str, Any]]] = {}
    errors: List[Dict[str, Any]] = []

    def run_step(
        bucket: str, scope: Dict[str, Any], action: Callable[[], Dict[str, Any]]
    ) -> None:
        try:
            result = action()
        except Exception as exc:  # pragma: no cover - defensive API boundary
            db.rollback()
            result = {"success": False, "message": str(exc)}

        entry = {"scope": scope, "result": result}
        results.setdefault(bucket, []).append(entry)
        if not result.get("success", False):
            errors.append(
                {
                    "target": bucket,
                    "scope": scope,
                    "message": result.get("message", "同步失败"),
                }
            )

    if "finance" in requested_targets:
        for pid in project_ids:
            run_step(
                "finance",
                {"project_id": pid},
                lambda pid=pid: service.sync_to_finance(
                    project_id=pid, year=year, month=month
                ),
            )

    if "rd" in requested_targets:
        for rd_project_id in rd_project_ids:
            run_step(
                "rd",
                {"rd_project_id": rd_project_id},
                lambda rd_project_id=rd_project_id: service.sync_to_rd(
                    rd_project_id=rd_project_id, year=year, month=month
                ),
            )

    if "project" in requested_targets:
        for timesheet in timesheets:
            if not timesheet.project_id:
                continue
            run_step(
                "project",
                {"timesheet_id": timesheet.id, "project_id": timesheet.project_id},
                lambda timesheet_id=timesheet.id: service.sync_to_project(
                    timesheet_id=timesheet_id
                ),
            )

    if "hr" in requested_targets:
        run_step(
            "hr",
            {"year": year, "month": month},
            lambda: service.sync_to_hr(year=year, month=month),
        )

    data = {
        "year": year,
        "month": month,
        "sync_target": target,
        "approved_timesheets": len(timesheets),
        "project_ids": project_ids,
        "rd_project_ids": rd_project_ids,
        "results": results,
        "failed_count": len(errors),
        "errors": errors,
        "requested_by": current_user.id,
    }
    message = "同步完成" if not errors else "同步完成，部分项目失败"
    return ResponseModel(code=200, message=message, data=data)
