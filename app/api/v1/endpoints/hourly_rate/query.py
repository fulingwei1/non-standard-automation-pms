# -*- coding: utf-8 -*-
"""
时薪查询API
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/users/{user_id}/hourly-rate", response_model=ResponseModel)
def get_user_hourly_rate(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    work_date: Optional[str] = Query(None, description="工作日期（YYYY-MM-DD格式），默认今天"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    获取用户时薪（按优先级：用户配置 > 角色配置 > 部门配置 > 默认配置）
    """
    from datetime import datetime

    from app.services.hourly_rate_service import HourlyRateService

    work_date_obj = None
    if work_date:
        try:
            work_date_obj = datetime.strptime(work_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")

    hourly_rate = HourlyRateService.get_user_hourly_rate(db, user_id, work_date_obj)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "user_id": user_id,
            "hourly_rate": float(hourly_rate),
            "work_date": work_date or str(date.today()),
            "source": "配置"
        }
    )


@router.post("/users/batch-hourly-rates", response_model=ResponseModel)
def get_users_hourly_rates(
    *,
    db: Session = Depends(deps.get_db),
    user_ids: List[int] = Query(..., description="用户ID列表"),
    work_date: Optional[str] = Query(None, description="工作日期（YYYY-MM-DD格式），默认今天"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    批量获取多个用户的时薪
    """
    from datetime import datetime

    from app.services.hourly_rate_service import HourlyRateService

    work_date_obj = None
    if work_date:
        try:
            work_date_obj = datetime.strptime(work_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")

    hourly_rates = HourlyRateService.get_users_hourly_rates(db, user_ids, work_date_obj)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "work_date": work_date or str(date.today()),
            "hourly_rates": {
                str(user_id): float(rate)
                for user_id, rate in hourly_rates.items()
            }
        }
    )


@router.get("/history", response_model=ResponseModel)
def get_hourly_rate_history(
    *,
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    role_id: Optional[int] = Query(None, description="角色ID筛选"),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD格式）"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    获取时薪配置历史记录
    """
    from datetime import datetime

    from app.services.hourly_rate_service import HourlyRateService

    start_date_obj = None
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误，应为YYYY-MM-DD")

    end_date_obj = None
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误，应为YYYY-MM-DD")

    history = HourlyRateService.get_hourly_rate_history(
        db, user_id, role_id, dept_id, start_date_obj, end_date_obj
    )

    # 转换日期为字符串
    for item in history:
        if item.get("effective_date"):
            item["effective_date"] = str(item["effective_date"])
        if item.get("expiry_date"):
            item["expiry_date"] = str(item["expiry_date"])
        if item.get("created_at"):
            item["created_at"] = item["created_at"].isoformat() if hasattr(item["created_at"], "isoformat") else str(item["created_at"])
        if item.get("updated_at"):
            item["updated_at"] = item["updated_at"].isoformat() if hasattr(item["updated_at"], "isoformat") else str(item["updated_at"])
        if item.get("hourly_rate"):
            item["hourly_rate"] = float(item["hourly_rate"])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "history": history,
            "total": len(history)
        }
    )
