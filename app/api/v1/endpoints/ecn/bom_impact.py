# -*- coding: utf-8 -*-
"""
ECN分析 - BOM影响分析

包含BOM影响分析和汇总
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import EcnBomImpact
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.ecn_bom_analysis_service import EcnBomAnalysisService

router = APIRouter()


@router.post("/ecns/{ecn_id}/analyze-bom-impact", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def analyze_bom_impact(
    ecn_id: int,
    machine_id: Optional[int] = Query(None, description="设备ID（可选，如果ECN已关联设备则自动获取）"),
    include_cascade: bool = Query(True, description="是否包含级联影响分析"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    BOM影响分析
    分析ECN对BOM的级联影响，包括直接影响和级联影响
    """
    try:
        service = EcnBomAnalysisService(db)
        result = service.analyze_bom_impact(
            ecn_id=ecn_id,
            machine_id=machine_id,
            include_cascade=include_cascade
        )

        return ResponseModel(
            code=200,
            message="BOM影响分析完成",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/ecns/{ecn_id}/bom-impact-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_bom_impact_summary(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取BOM影响汇总
    """
    bom_impacts = db.query(EcnBomImpact).filter(
        EcnBomImpact.ecn_id == ecn_id
    ).all()

    if not bom_impacts:
        return ResponseModel(
            code=200,
            message="暂无BOM影响分析结果",
            data={
                "ecn_id": ecn_id,
                "has_impact": False
            }
        )

    total_cost = sum(float(impact.total_cost_impact or 0) for impact in bom_impacts)
    total_items = sum(impact.affected_item_count or 0 for impact in bom_impacts)
    max_schedule = max((impact.schedule_impact_days or 0 for impact in bom_impacts), default=0)

    return ResponseModel(
        code=200,
        message="获取BOM影响汇总成功",
        data={
            "ecn_id": ecn_id,
            "has_impact": True,
            "total_cost_impact": total_cost,
            "total_affected_items": total_items,
            "max_schedule_impact_days": max_schedule,
            "impacts": [
                {
                    "id": impact.id,
                    "bom_level": impact.bom_level,
                    "affected_item_count": impact.affected_item_count,
                    "total_cost_impact": float(impact.total_cost_impact or 0),
                    "schedule_impact_days": impact.schedule_impact_days,
                    "impact_type": impact.impact_type,
                    "analysis_note": impact.analysis_note
                }
                for impact in bom_impacts
            ]
        }
    )
