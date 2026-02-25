# -*- coding: utf-8 -*-
"""
齐套分析 - 优化建议
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models import MaterialReadiness
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/analysis/{readiness_id}/optimize", response_model=ResponseModel)
async def get_optimization_suggestions(
    readiness_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取齐套分析优化建议"""
    from app.services.assembly_kit_optimizer import AssemblyKitOptimizer

    readiness = get_or_404(db, MaterialReadiness, readiness_id, "齐套分析记录不存在")

    suggestions = AssemblyKitOptimizer.generate_optimization_suggestions(db, readiness)
    optimized_date = AssemblyKitOptimizer.optimize_estimated_ready_date(db, readiness)

    return ResponseModel(
        code=200,
        message="优化建议获取成功",
        data={
            "suggestions": suggestions,
            "optimized_ready_date": optimized_date.isoformat() if optimized_date else None,
            "current_ready_date": readiness.estimated_ready_date.isoformat() if readiness.estimated_ready_date else None
        }
    )
