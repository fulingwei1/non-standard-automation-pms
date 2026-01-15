# -*- coding: utf-8 -*-
"""
部门经理评价 API 端点
"""

from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.performance import PerformancePeriod, PerformanceResult
from app.services.manager_evaluation_service import ManagerEvaluationService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/manager-evaluation", tags=["部门经理评价"])


class AdjustPerformanceRequest(BaseModel):
    """调整绩效请求"""
    result_id: int = Field(..., description="绩效结果ID")
    new_total_score: Optional[float] = Field(None, description="新的综合得分")
    new_dept_rank: Optional[int] = Field(None, description="新的部门排名")
    new_company_rank: Optional[int] = Field(None, description="新的公司排名")
    adjustment_reason: str = Field(..., min_length=10, description="调整理由（必填，至少10个字符）")


class SubmitEvaluationRequest(BaseModel):
    """提交评价请求"""
    result_id: int = Field(..., description="绩效结果ID")
    overall_comment: Optional[str] = Field(None, description="总体评价")
    strength_comment: Optional[str] = Field(None, description="优点评价")
    improvement_comment: Optional[str] = Field(None, description="改进建议")


@router.post("/adjust", summary="调整绩效得分和排名")
async def adjust_performance(
    request: AdjustPerformanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """部门经理调整工程师的绩效得分和排名"""
    service = ManagerEvaluationService(db)

    try:
        result = service.adjust_performance(
            result_id=request.result_id,
            manager_id=current_user.id,
            new_total_score=Decimal(str(request.new_total_score)) if request.new_total_score else None,
            new_dept_rank=request.new_dept_rank,
            new_company_rank=request.new_company_rank,
            adjustment_reason=request.adjustment_reason
        )

        return ResponseModel(
            code=200,
            message="绩效调整成功",
            data={
                'result_id': result.id,
                'total_score': float(result.total_score or 0),
                'dept_rank': result.dept_rank,
                'company_rank': result.company_rank,
                'is_adjusted': result.is_adjusted
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/adjustment-history/{result_id}", summary="获取调整历史")
async def get_adjustment_history(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取绩效调整历史记录（增强版：包含详细信息）"""
    service = ManagerEvaluationService(db)

    history = service.get_adjustment_history(result_id)

    return ResponseModel(
        code=200,
        message="获取调整历史成功",
        data=history
    )


@router.get("/evaluation-tasks", summary="获取评价任务列表")
async def get_evaluation_tasks(
    period_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部门经理需要评价的任务列表"""
    service = ManagerEvaluationService(db)

    tasks = service.get_manager_evaluation_tasks(
        manager_id=current_user.id,
        period_id=period_id
    )

    return ResponseModel(
        code=200,
        message="获取评价任务成功",
        data=[
            {
                'result_id': t.id,
                'engineer_id': t.user_id,
                'engineer_name': t.user_name,
                'total_score': float(t.total_score or 0),
                'level': t.level,
                'dept_rank': t.dept_rank,
                'is_adjusted': t.is_adjusted
            }
            for t in tasks
        ]
    )


@router.post("/submit-evaluation", summary="提交评价（不调整得分）")
async def submit_evaluation(
    request: SubmitEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """部门经理提交评价（不调整得分和排名）"""
    service = ManagerEvaluationService(db)

    try:
        result = service.submit_evaluation(
            result_id=request.result_id,
            manager_id=current_user.id,
            overall_comment=request.overall_comment,
            strength_comment=request.strength_comment,
            improvement_comment=request.improvement_comment
        )

        return ResponseModel(
            code=200,
            message="评价提交成功",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/engineers", summary="获取可评价的工程师列表")
async def get_engineers_for_evaluation(
    period_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部门经理可评价的工程师列表"""
    service = ManagerEvaluationService(db)

    try:
        engineers = service.get_engineers_for_evaluation(
            manager_id=current_user.id,
            period_id=period_id
        )

        return ResponseModel(
            code=200,
            message="获取工程师列表成功",
            data=engineers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
