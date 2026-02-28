# -*- coding: utf-8 -*-
"""
会议报表 - 统一报表框架端点
"""

import logging
from calendar import monthrange
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.report_framework import ConfigError
from app.services.report_framework.engine import (
    ParameterError,
    PermissionError,
    ReportEngine,
)

router = APIRouter(
    prefix="/reports-unified",
    tags=["meeting-reports-unified"],
)

logger = logging.getLogger(__name__)


@router.get("/meeting-monthly", response_model=ResponseModel)
def get_meeting_monthly_report_unified(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份（1-12）"),
    rhythm_level: Optional[str] = Query(
        None,
        description="节律层级（可选：STRATEGIC/TACTICAL/OPERATIONAL）",
    ),
    format: str = Query("json", description="导出格式，目前仅支持json"),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel:
    """
    使用统一报表框架生成会议月报
    """
    if format.lower() != "json":
        raise HTTPException(status_code=400, detail="目前仅支持JSON格式")

    try:
        period_start = date(year, month, 1)
    except ValueError:
        raise HTTPException(status_code=422, detail="无效的年份或月份")

    period_end = date(year, month, monthrange(year, month)[1])

    try:
        engine = ReportEngine(db)
        result = engine.generate(
            report_code="MEETING_MONTHLY",
            params={
                "year": year,
                "month": month,
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat(),
                "rhythm_level": rhythm_level,
            },
            format="json",
            user=current_user,
            skip_cache=False,
        )
        return ResponseModel(
            code=200,
            message="success",
            data=result.data,
        )

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("生成会议月报失败: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"生成会议月报失败: {str(e)}",
        )
