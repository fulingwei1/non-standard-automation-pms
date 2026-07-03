# -*- coding: utf-8 -*-
"""工时质量检查兼容接口。"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.timesheet.timesheet_quality_service import TimesheetQualityService

router = APIRouter(tags=["timesheet-quality"])


@router.get("/anomalies", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def detect_timesheet_anomalies(
    *,
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """检测工时异常，供旧仪表板 `/timesheet/anomalies` 使用。"""
    service = TimesheetQualityService(db)
    anomalies = service.detect_anomalies(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
    )
    return ResponseModel(code=200, message="success", data=anomalies)
