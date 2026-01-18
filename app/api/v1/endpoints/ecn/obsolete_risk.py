# -*- coding: utf-8 -*-
"""
ECN分析 - 呆滞料风险

包含呆滞料风险检查和预警
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import EcnAffectedMaterial
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.ecn_bom_analysis_service import EcnBomAnalysisService

router = APIRouter()


@router.post("/ecns/{ecn_id}/check-obsolete-risk", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def check_obsolete_material_risk(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查呆滞料风险
    分析ECN变更可能导致呆滞的物料
    """
    try:
        service = EcnBomAnalysisService(db)
        result = service.check_obsolete_material_risk(ecn_id=ecn_id)

        return ResponseModel(
            code=200,
            message="呆滞料风险检查完成",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


@router.get("/ecns/{ecn_id}/obsolete-material-alerts", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_obsolete_material_alerts(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取呆滞料预警列表
    """
    affected_materials = db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn_id,
        EcnAffectedMaterial.is_obsolete_risk == True
    ).all()

    alerts = []
    for mat in affected_materials:
        alerts.append({
            "material_id": mat.material_id,
            "material_code": mat.material_code,
            "material_name": mat.material_name,
            "change_type": mat.change_type,
            "obsolete_quantity": float(mat.obsolete_quantity or 0),
            "obsolete_cost": float(mat.obsolete_cost or 0),
            "risk_level": mat.obsolete_risk_level,
            "analysis": mat.obsolete_analysis
        })

    return ResponseModel(
        code=200,
        message="获取呆滞料预警成功",
        data={
            "ecn_id": ecn_id,
            "alerts": alerts,
            "total_count": len(alerts),
            "total_cost": sum(float(mat.obsolete_cost or 0) for mat in affected_materials)
        }
    )
