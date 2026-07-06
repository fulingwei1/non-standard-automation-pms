# -*- coding: utf-8 -*-
"""售前智能体使用反馈 API。

让销售反馈AI产出的使用效果，形成数据闭环：
  POST /presale-usage-feedback          提交反馈
  GET  /presale-usage-feedback          查看反馈列表
  GET  /presale-usage-feedback/stats    统计使用效果
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale_usage_feedback import PresaleUsageFeedback
from app.models.user import User

router = APIRouter(prefix="/presale-usage-feedback", tags=["售前智能体使用反馈"])


class UsageFeedbackCreate(BaseModel):
    """提交使用反馈"""
    proposal_id: Optional[int] = Field(None, description="关联的方案ID")
    audit_pack_id: Optional[int] = Field(None, description="关联的验厂资料ID")
    coach_session_id: Optional[int] = Field(None, description="关联的销售教练会话ID")
    usage_scenario: str = Field(..., description="使用场景（方案生成/验厂资料/销售教练/竞争分析）")
    used: int = Field(1, description="是否使用了AI产出（1=用了 0=没用）")
    outcome: Optional[str] = Field(None, description="结果（成单/未成单/部分采用/进行中）")
    customer_feedback: Optional[str] = Field(None, description="客户反馈（接受/拒绝/修改/无反馈）")
    rating: Optional[int] = Field(None, ge=1, le=5, description="销售评分（1-5分）")
    rating_comment: Optional[str] = Field(None, description="评分说明")
    improvement_suggestion: Optional[str] = Field(None, description="改进建议")


@router.post("", summary="提交使用反馈")
def create_usage_feedback(
    feedback: UsageFeedbackCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售提交AI产出的使用反馈，形成数据闭环。"""
    record = PresaleUsageFeedback(
        proposal_id=feedback.proposal_id,
        audit_pack_id=feedback.audit_pack_id,
        coach_session_id=feedback.coach_session_id,
        usage_scenario=feedback.usage_scenario,
        used=feedback.used,
        outcome=feedback.outcome,
        customer_feedback=feedback.customer_feedback,
        rating=feedback.rating,
        rating_comment=feedback.rating_comment,
        improvement_suggestion=feedback.improvement_suggestion,
        submitted_by=current_user.id,
        submitted_by_name=getattr(current_user, "full_name", None) or current_user.username,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "message": "反馈提交成功，感谢帮助AI改进"}


@router.get("", summary="查看反馈列表")
def list_usage_feedback(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查看使用反馈列表。"""
    records = (
        db.query(PresaleUsageFeedback)
        .order_by(desc(PresaleUsageFeedback.created_at))
        .limit(limit)
        .all()
    )
    return {"total": len(records), "items": [r.to_dict() for r in records]}


@router.get("/stats", summary="统计使用效果")
def usage_feedback_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """统计AI使用效果，衡量业务价值。"""
    total = db.query(func.count(PresaleUsageFeedback.id)).scalar() or 0
    
    if total == 0:
        return {
            "total_feedback": 0,
            "message": "暂无反馈数据",
        }
    
    # 使用率
    used_count = db.query(func.count(PresaleUsageFeedback.id)).filter(
        PresaleUsageFeedback.used == 1
    ).scalar() or 0
    usage_rate = round(used_count / total * 100, 1) if total > 0 else 0
    
    # 成单率
    won_count = db.query(func.count(PresaleUsageFeedback.id)).filter(
        PresaleUsageFeedback.outcome == "成单"
    ).scalar() or 0
    win_rate = round(won_count / used_count * 100, 1) if used_count > 0 else 0
    
    # 平均评分
    avg_rating = db.query(func.avg(PresaleUsageFeedback.rating)).filter(
        PresaleUsageFeedback.rating.isnot(None)
    ).scalar()
    avg_rating = round(avg_rating, 1) if avg_rating else None
    
    # 按场景统计
    scenario_stats = {}
    for scenario in ["方案生成", "验厂资料", "销售教练", "竞争分析"]:
        count = db.query(func.count(PresaleUsageFeedback.id)).filter(
            PresaleUsageFeedback.usage_scenario == scenario
        ).scalar() or 0
        scenario_stats[scenario] = count
    
    # 按结果统计
    outcome_stats = {}
    for outcome in ["成单", "未成单", "部分采用", "进行中"]:
        count = db.query(func.count(PresaleUsageFeedback.id)).filter(
            PresaleUsageFeedback.outcome == outcome
        ).scalar() or 0
        outcome_stats[outcome] = count
    
    return {
        "total_feedback": total,
        "usage_rate": usage_rate,
        "win_rate": win_rate,
        "avg_rating": avg_rating,
        "by_scenario": scenario_stats,
        "by_outcome": outcome_stats,
    }
