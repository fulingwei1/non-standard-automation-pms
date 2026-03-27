# -*- coding: utf-8 -*-
"""
最佳实践自动归纳 API
基于高绩效、按时交付、预算控制良好的项目自动归纳最佳实践
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.knowledge.induction_service import BestPracticeInductionService

router = APIRouter()


@router.post("/induce-best-practices", response_model=ResponseModel)
def induce_best_practices(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    自动归纳最佳实践

    分析所有已结项项目，从以下维度归纳：
    - 高绩效项目的共同特征
    - 按时交付项目的管理做法
    - 预算控制良好的项目经验
    """
    service = BestPracticeInductionService(db)
    result = service.induce(created_by=current_user.id)

    db.commit()

    entries_data = [
        {
            "id": e.id,
            "entry_code": e.entry_code,
            "title": e.title,
            "summary": e.summary,
        }
        for e in result["entries"]
    ]

    return ResponseModel(
        code=200,
        message=f"分析了 {result['total_projects_analyzed']} 个项目，归纳 {result['best_practices_generated']} 条最佳实践",
        data={
            "total_projects_analyzed": result["total_projects_analyzed"],
            "high_perf_projects": result["high_perf_projects"],
            "on_time_projects": result["on_time_projects"],
            "budget_controlled_projects": result["budget_controlled_projects"],
            "best_practices_generated": result["best_practices_generated"],
            "entries": entries_data,
        },
    )
