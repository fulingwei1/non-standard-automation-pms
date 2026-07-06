# -*- coding: utf-8 -*-
"""
PM 月度自检 API（对应手册 Sheet8）

GET /pmo/pm-monthly-check        所有 PM 的月度自检汇总
GET /pmo/pm-monthly-check?pm_id=X 指定 PM 的月度自检
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/pmo/pm-monthly-check", tags=["PM月度自检"])


@router.get("", response_model=ResponseModel, summary="PM 月度自检（手册 Sheet8）")
def pm_monthly_check(
    pm_id: Optional[int] = Query(None, description="指定 PM 用户ID（不传则汇总所有）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """PM 月度自检表：在管项目利润健康度 + 8项关键动作自动判定。

    对应《项目经理毛利率提升操作手册》Sheet8。
    实时聚合，不入库。4项动作系统自动判定，4项靠PM手填。
    """
    from app.services.dashboard.pm_monthly_check_service import (
        PmMonthlyCheckService,
    )

    result = PmMonthlyCheckService(db).get_check(pm_id=pm_id)
    s = result["summary"]
    return ResponseModel(
        code=200,
        message=(
            f"PM月度自检（{result['period']['year']}年{result['period']['month']}月）："
            f"{s['total_projects']} 个在管项目，"
            f"healthy {s['healthy']}/warning {s['warning']}/critical {s['critical']}，"
            f"{s['auto_failed_actions']} 项动作需关注"
        ),
        data=result,
    )
