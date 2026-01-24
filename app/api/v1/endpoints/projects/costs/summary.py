# -*- coding: utf-8 -*-
"""
项目成本汇总（自定义端点）

保留原有的成本汇总功能
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectCost
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/summary", response_model=ResponseModel)
def get_project_cost_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """获取项目成本汇总"""
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 按类型汇总
    type_summary = (
        db.query(ProjectCost.cost_type, func.sum(ProjectCost.amount).label("total"))
        .filter(ProjectCost.project_id == project_id)
        .group_by(ProjectCost.cost_type)
        .all()
    )

    # 总成本
    total_cost = (
        db.query(func.sum(ProjectCost.amount))
        .filter(ProjectCost.project_id == project_id)
        .scalar()
        or Decimal("0")
    )

    return ResponseModel(
        data={
            "project_id": project_id,
            "project_name": project.project_name,
            "total_cost": float(total_cost),
            "by_type": {t.cost_type: float(t.total) for t in type_summary},
            "budget": float(project.budget_amount) if project.budget_amount else None,
            "budget_used_pct": (
                round(float(total_cost) / float(project.budget_amount) * 100, 2)
                if project.budget_amount and project.budget_amount > 0
                else None
            ),
        }
    )
