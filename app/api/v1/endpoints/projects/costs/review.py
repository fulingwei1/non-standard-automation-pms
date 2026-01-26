# -*- coding: utf-8 -*-
"""
项目成本复盘模块

提供项目成本复盘报告生成功能。
路由: /projects/{project_id}/costs/review
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/generate-cost-review", response_model=ResponseModel)
def generate_cost_review(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    手动触发生成项目成本复盘报告
    """
    from app.services.cost_review_service import CostReviewService

    try:
        review = CostReviewService.generate_cost_review_report(
            db, project_id, current_user.id
        )
        db.commit()
        db.refresh(review)

        return ResponseModel(
            code=200,
            message="成本复盘报告生成成功",
            data={
                "review_id": review.id,
                "review_no": review.review_no,
                "project_id": project_id,
                "budget_amount": float(review.budget_amount or 0),
                "actual_cost": float(review.actual_cost or 0),
                "cost_variance": float(review.cost_variance or 0)
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成成本复盘报告失败：{str(e)}")
