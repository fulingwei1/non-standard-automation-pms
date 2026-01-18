# -*- coding: utf-8 -*-
"""
ECN分析 - 责任分摊

包含责任分摊分析和汇总
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn, EcnResponsibility
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/ecns/{ecn_id}/responsibility-analysis", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_responsibility_analysis(
    ecn_id: int,
    responsibilities: List[Dict[str, Any]] = Body(..., description="责任分摊列表"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建责任分摊分析
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail=f"ECN {ecn_id} 不存在")

    # 验证责任比例总和
    total_ratio = sum(float(r.get('responsibility_ratio', 0)) for r in responsibilities)
    if abs(total_ratio - 100) > 0.01:
        raise HTTPException(status_code=400, detail=f"责任比例总和必须为100%，当前为{total_ratio}%")

    # 删除旧的责任分摊
    db.query(EcnResponsibility).filter(EcnResponsibility.ecn_id == ecn_id).delete()

    # 创建新的责任分摊
    created_responsibilities = []
    total_cost = float(ecn.cost_impact or 0)

    for resp_data in responsibilities:
        ratio = float(resp_data.get('responsibility_ratio', 0))
        cost_allocation = total_cost * ratio / 100

        responsibility = EcnResponsibility(
            ecn_id=ecn_id,
            dept=resp_data.get('dept'),
            responsibility_ratio=ratio,
            responsibility_type=resp_data.get('responsibility_type', 'PRIMARY'),
            cost_allocation=cost_allocation,
            impact_description=resp_data.get('impact_description'),
            responsibility_scope=resp_data.get('responsibility_scope'),
            confirmed=False
        )
        db.add(responsibility)
        created_responsibilities.append(responsibility)

    db.commit()

    return ResponseModel(
        code=200,
        message="责任分摊分析创建成功",
        data={
            "ecn_id": ecn_id,
            "created_count": len(created_responsibilities),
            "responsibilities": [
                {
                    "id": r.id,
                    "dept": r.dept,
                    "responsibility_ratio": float(r.responsibility_ratio),
                    "cost_allocation": float(r.cost_allocation),
                    "responsibility_type": r.responsibility_type
                }
                for r in created_responsibilities
            ]
        }
    )


@router.get("/ecns/{ecn_id}/responsibility-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_responsibility_summary(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取责任分摊汇总
    """
    responsibilities = db.query(EcnResponsibility).filter(
        EcnResponsibility.ecn_id == ecn_id
    ).all()

    if not responsibilities:
        return ResponseModel(
            code=200,
            message="暂无责任分摊信息",
            data={
                "ecn_id": ecn_id,
                "has_responsibility": False
            }
        )

    total_cost = sum(float(r.cost_allocation or 0) for r in responsibilities)

    return ResponseModel(
        code=200,
        message="获取责任分摊汇总成功",
        data={
            "ecn_id": ecn_id,
            "has_responsibility": True,
            "total_cost_allocation": total_cost,
            "responsibilities": [
                {
                    "id": r.id,
                    "dept": r.dept,
                    "responsibility_ratio": float(r.responsibility_ratio),
                    "responsibility_type": r.responsibility_type,
                    "cost_allocation": float(r.cost_allocation),
                    "impact_description": r.impact_description,
                    "confirmed": r.confirmed,
                    "confirmed_at": r.confirmed_at.isoformat() if r.confirmed_at else None
                }
                for r in responsibilities
            ]
        }
    )
