# -*- coding: utf-8 -*-
"""销售统计 - 报价统计。"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.quote_statistics_service import QuoteStatisticsService

router = APIRouter()


@router.get("/statistics/quote-stats", response_model=ResponseModel)
def get_quote_stats(
    db: Session = Depends(deps.get_db),
    time_range: Optional[str] = Query("month", description="时间范围: week/month/quarter/year"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价统计数据
    """
    data = QuoteStatisticsService(db).get_statistics(
        current_user=current_user,
        time_range=time_range,
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            **data,
            "thisMonth": data.get("currentPeriod", 0),
            "lastMonth": data.get("previousPeriod", 0),
        },
    )
