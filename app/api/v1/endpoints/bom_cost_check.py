# -*- coding: utf-8 -*-
"""
BOM 成本检查清单 API（对应手册 Sheet3）

GET /projects/{project_id}/bom-cost-check  项目的 BOM 成本检查清单
"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/projects", tags=["BOM成本检查"])


@router.get(
    "/{project_id}/bom-cost-check",
    response_model=ResponseModel,
    summary="BOM 成本检查清单（手册 Sheet3）",
)
def bom_cost_check(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """BOM 成本检查清单：12 项检查（2 项自动判定 + 10 项 PM 勾选）。

    自动判定：
    - 历史比价：关键物料单价 vs 历史均价，偏差>15% 预警
    - 同类项目对比：同类项目 BOM 总成本偏差>10% 预警

    对应《项目经理毛利率提升操作手册》Sheet3。
    """
    from app.services.dashboard.bom_cost_check_service import BomCostCheckService

    result = BomCostCheckService(db).get_check(project_id)
    if "error" in result:
        return ResponseModel(code=404, message=result["error"], data=result)
    s = result.get("summary", {})
    return ResponseModel(
        code=200,
        message=(
            f"BOM 成本检查：{result.get('bom_item_count', 0)} 项物料，"
            f"自动判定 {s.get('auto_passed', 0)} 通过/{s.get('auto_failed', 0)} 需关注，"
            f"{s.get('manual_pending', 0)} 项待 PM 勾选"
        ),
        data=result,
    )
