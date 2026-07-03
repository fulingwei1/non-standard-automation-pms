# -*- coding: utf-8 -*-
"""AI 产出反馈端点：记录采纳/驳回 + 采纳率统计。

前端在任何 AI 建议卡片上放"采纳/驳回"两个按钮打到 POST /ai-feedback 即接入闭环；
GET /ai-feedback/stats 供经营侧复盘各 AI 功能的真实采纳率。
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services import ai_feedback_service

router = APIRouter(prefix="/ai-feedback", tags=["AI反馈"])


class FeedbackRequest(BaseModel):
    feature_key: str = Field(..., description="AI 功能标识，如 three_tier_quotation")
    verdict: str = Field(..., description="ADOPTED/REJECTED/PARTIAL")
    ref_type: Optional[str] = Field(None, description="产出对象类型")
    ref_id: Optional[int] = Field(None, description="产出对象ID")
    reason: Optional[str] = Field(None, description="采纳/驳回原因")
    detail: Optional[Dict[str, Any]] = Field(None, description="补充信息")


@router.post("", summary="记录 AI 产出反馈")
def record_feedback(
    request: FeedbackRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        feedback = ai_feedback_service.record(
            db,
            feature_key=request.feature_key,
            verdict=request.verdict,
            ref_type=request.ref_type,
            ref_id=request.ref_id,
            reason=request.reason,
            detail=request.detail,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"feedback_id": feedback.id, "feature_key": feedback.feature_key, "verdict": feedback.verdict}


@router.get("/stats", summary="AI 功能采纳率统计")
def feedback_stats(
    feature_key: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return {"items": ai_feedback_service.stats(db, feature_key=feature_key)}
