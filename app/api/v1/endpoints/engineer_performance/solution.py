# -*- coding: utf-8 -*-
"""
方案工程师专用 API 端点
"""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.performance import PerformancePeriod
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.solution_engineer_bonus_service import SolutionEngineerBonusService

router = APIRouter(prefix="/solution", tags=["方案工程师"])


@router.get("/{engineer_id}/score", summary="获取方案工程师得分详情")
async def get_solution_score_details(
    engineer_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取方案工程师六维得分详情"""
    service = SolutionEngineerBonusService(db)

    try:
        details = service.get_solution_score_details(engineer_id, period_id)
        return ResponseModel(
            code=200,
            message="获取得分详情成功",
            data=details
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{engineer_id}/bonus", summary="获取方案工程师奖金详情")
async def get_solution_bonus_details(
    engineer_id: int,
    period_id: int,
    base_bonus_per_solution: Optional[float] = Query(500.0, description="每个方案基础奖金"),
    won_bonus_ratio: Optional[float] = Query(0.001, description="中标奖金比例"),
    high_quality_compensation: Optional[float] = Query(300.0, description="高质量方案补偿"),
    success_rate_bonus: Optional[float] = Query(2000.0, description="成功率奖励"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取方案工程师奖金计算详情"""
    service = SolutionEngineerBonusService(db)

    try:
        bonus_details = service.calculate_solution_bonus(
            engineer_id=engineer_id,
            period_id=period_id,
            base_bonus_per_solution=Decimal(str(base_bonus_per_solution)),
            won_bonus_ratio=Decimal(str(won_bonus_ratio)),
            high_quality_compensation=Decimal(str(high_quality_compensation)),
            success_rate_bonus=Decimal(str(success_rate_bonus))
        )
        return ResponseModel(
            code=200,
            message="获取奖金详情成功",
            data=bonus_details
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CalculateBonusRequest(BaseModel):
    """计算奖金请求"""
    engineer_id: int = Field(..., description="工程师ID")
    period_id: int = Field(..., description="考核周期ID")
    base_bonus_per_solution: Optional[float] = Field(500.0, description="每个方案基础奖金")
    won_bonus_ratio: Optional[float] = Field(0.001, description="中标奖金比例")
    high_quality_compensation: Optional[float] = Field(300.0, description="高质量方案补偿")
    success_rate_bonus: Optional[float] = Field(2000.0, description="成功率奖励")


@router.post("/calculate-bonus", summary="计算方案工程师奖金")
async def calculate_solution_bonus(
    request: CalculateBonusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """计算方案工程师奖金（方案完成奖金+中标奖金+高质量方案补偿+成功率奖励）"""
    service = SolutionEngineerBonusService(db)

    try:
        bonus_details = service.calculate_solution_bonus(
            engineer_id=request.engineer_id,
            period_id=request.period_id,
            base_bonus_per_solution=Decimal(str(request.base_bonus_per_solution)),
            won_bonus_ratio=Decimal(str(request.won_bonus_ratio)),
            high_quality_compensation=Decimal(str(request.high_quality_compensation)),
            success_rate_bonus=Decimal(str(request.success_rate_bonus))
        )
        return ResponseModel(
            code=200,
            message="奖金计算完成",
            data=bonus_details
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
