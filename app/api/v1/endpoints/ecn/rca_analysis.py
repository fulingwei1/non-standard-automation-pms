# -*- coding: utf-8 -*-
"""
ECN分析 - RCA分析

包含根本原因分析和查询
"""

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.put("/ecns/{ecn_id}/rca-analysis", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_rca_analysis(
    ecn_id: int,
    root_cause: Optional[str] = Body(None, description="根本原因类型"),
    root_cause_analysis: Optional[str] = Body(None, description="RCA分析内容"),
    root_cause_category: Optional[str] = Body(None, description="原因分类"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新RCA分析
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail=f"ECN {ecn_id} 不存在")

    if root_cause is not None:
        ecn.root_cause = root_cause
    if root_cause_analysis is not None:
        ecn.root_cause_analysis = root_cause_analysis
    if root_cause_category is not None:
        ecn.root_cause_category = root_cause_category

    db.commit()

    return ResponseModel(
        code=200,
        message="RCA分析更新成功",
        data={
            "ecn_id": ecn_id,
            "root_cause": ecn.root_cause,
            "root_cause_analysis": ecn.root_cause_analysis,
            "root_cause_category": ecn.root_cause_category
        }
    )


@router.get("/ecns/{ecn_id}/rca-analysis", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rca_analysis(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取RCA分析
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail=f"ECN {ecn_id} 不存在")

    return ResponseModel(
        code=200,
        message="获取RCA分析成功",
        data={
            "ecn_id": ecn_id,
            "root_cause": ecn.root_cause,
            "root_cause_analysis": ecn.root_cause_analysis,
            "root_cause_category": ecn.root_cause_category
        }
    )
