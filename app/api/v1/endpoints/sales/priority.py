# -*- coding: utf-8 -*-
"""
销售线索优先级管理 API endpoints
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Lead, Opportunity
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.lead_priority_scoring import LeadPriorityScoringService

router = APIRouter()


@router.post("/leads/{lead_id}/calculate-priority", response_model=ResponseModel)
def calculate_lead_priority(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算线索优先级评分
    """
    service = LeadPriorityScoringService(db)

    try:
        result = service.calculate_lead_priority(lead_id)

        # 更新线索的优先级字段
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.priority_score = result['total_score']
            lead.is_key_lead = result['is_key_lead']
            lead.priority_level = result['priority_level']
            lead.importance_level = result['importance_level']
            lead.urgency_level = result['urgency_level']
            db.commit()

        return ResponseModel(
            code=200,
            message="计算成功",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/leads/priority-ranking", response_model=ResponseModel)
def get_lead_priority_ranking(
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索优先级排名
    """
    service = LeadPriorityScoringService(db)
    rankings = service.get_priority_ranking('lead', limit=limit)

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            'rankings': rankings,
            'total': len(rankings)
        }
    )


@router.get("/leads/key-leads", response_model=ResponseModel)
def get_key_leads(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取关键线索列表
    """
    service = LeadPriorityScoringService(db)
    key_leads = service.get_key_leads()

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            'key_leads': key_leads,
            'total': len(key_leads)
        }
    )


@router.post("/opportunities/{opp_id}/calculate-priority", response_model=ResponseModel)
def calculate_opportunity_priority(
    opp_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算商机优先级评分
    """
    service = LeadPriorityScoringService(db)

    try:
        result = service.calculate_opportunity_priority(opp_id)

        # 更新商机的优先级字段
        opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if opportunity:
            opportunity.priority_score = result['total_score']
            opportunity.is_key_opportunity = result['is_key_opportunity']
            opportunity.priority_level = result['priority_level']
            db.commit()

        return ResponseModel(
            code=200,
            message="计算成功",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/opportunities/priority-ranking", response_model=ResponseModel)
def get_opportunity_priority_ranking(
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取商机优先级排名
    """
    service = LeadPriorityScoringService(db)
    rankings = service.get_priority_ranking('opportunity', limit=limit)

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            'rankings': rankings,
            'total': len(rankings)
        }
    )


@router.get("/opportunities/key-opportunities", response_model=ResponseModel)
def get_key_opportunities(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取关键商机列表
    """
    service = LeadPriorityScoringService(db)
    key_opportunities = service.get_key_opportunities()

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            'key_opportunities': key_opportunities,
            'total': len(key_opportunities)
        }
    )
