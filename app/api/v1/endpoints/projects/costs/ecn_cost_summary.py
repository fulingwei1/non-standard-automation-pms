# -*- coding: utf-8 -*-
"""
项目ECN成本汇总端点

端点：
  GET /projects/{project_id}/costs/ecn-summary — 项目所有ECN成本汇总
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.ecn_cost_impact import ProjectEcnCostSummaryResponse
from app.services import ecn_cost_impact_service as service

router = APIRouter()


@router.get(
    "/ecn-summary",
    response_model=ProjectEcnCostSummaryResponse,
    summary="项目ECN成本汇总",
    description="汇总项目下所有ECN的成本，按ECN分类、按成本类型统计，计算ECN成本占项目预算比例",
)
def get_project_ecn_cost_summary(
    project_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        return service.get_project_ecn_cost_summary(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
