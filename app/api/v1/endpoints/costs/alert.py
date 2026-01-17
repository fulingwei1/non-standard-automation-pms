"""
成本预警

提供项目预算执行预警功能。
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/projects/{project_id}/check-budget-alert", response_model=ResponseModel)
def check_project_budget_alert(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    手动检查项目预算执行情况并生成预警
    """
    from app.services.cost_alert_service import CostAlertService

    try:
        alert = CostAlertService.check_budget_execution(db, project_id)
        db.commit()

        if alert:
            return ResponseModel(
                code=200,
                message="已生成成本预警",
                data={
                    "alert_id": alert.id,
                    "alert_no": alert.alert_no,
                    "alert_level": alert.alert_level,
                    "alert_title": alert.alert_title,
                    "alert_content": alert.alert_content
                }
            )
        else:
            return ResponseModel(
                code=200,
                message="预算执行情况正常，无需预警",
                data=None
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查预算预警失败：{str(e)}")


@router.post("/check-all-projects-budget", response_model=ResponseModel)
def check_all_projects_budget(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: Optional[List[int]] = Body(None, description="项目ID列表（不提供则检查所有活跃项目）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    批量检查项目预算执行情况
    """
    from app.services.cost_alert_service import CostAlertService

    try:
        result = CostAlertService.check_all_projects_budget(db, project_ids)
        db.commit()

        return ResponseModel(
            code=200,
            message=f"检查完成，共检查{result['checked_count']}个项目，生成{result['alert_count']}个预警",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量检查预算预警失败：{str(e)}")
