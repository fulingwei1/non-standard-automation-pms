# -*- coding: utf-8 -*-
"""
变更影响智能分析 API端点
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.dependencies import get_db
from app.models import ChangeImpactAnalysis, ChangeRequest, ChangeResponseSuggestion, User
from app.schemas.change_impact import (
    ChangeImpactAnalysisResponse,
    ChangeResponseSuggestionResponse,
    ChainReactionResponse,
    SuggestionGenerateRequest,
    SuggestionSelectRequest,
)
from app.services.change_impact_ai_service import ChangeImpactAIService
from app.services.change_response_suggestion_service import ChangeResponseSuggestionService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 变更影响分析 API
# ============================================================

@router.post("/changes/{change_id}/analyze", response_model=ChangeImpactAnalysisResponse)
async def analyze_change_impact(
    change_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """触发变更影响分析"""
    try:
        service = ChangeImpactAIService(db)
        analysis = await service.analyze_change_impact(change_id, current_user.id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"变更影响分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/changes/{change_id}/impact", response_model=ChangeImpactAnalysisResponse)
async def get_change_impact(
    change_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取变更影响分析结果"""
    # 获取最新的分析结果
    analysis = db.query(ChangeImpactAnalysis).filter(
        ChangeImpactAnalysis.change_request_id == change_id
    ).order_by(ChangeImpactAnalysis.created_at.desc()).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="未找到影响分析结果")
    
    return analysis


@router.get("/changes/{change_id}/chain-reactions", response_model=ChainReactionResponse)
async def get_chain_reactions(
    change_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取连锁反应分析"""
    analysis = db.query(ChangeImpactAnalysis).filter(
        ChangeImpactAnalysis.change_request_id == change_id
    ).order_by(ChangeImpactAnalysis.created_at.desc()).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="未找到影响分析结果")
    
    return ChainReactionResponse(
        change_request_id=change_id,
        detected=analysis.chain_reaction_detected or False,
        depth=analysis.chain_reaction_depth or 0,
        affected_tasks=analysis.schedule_affected_tasks or [],
        affected_milestones=analysis.schedule_affected_milestones or [],
        affected_projects=analysis.chain_reaction_affected_projects or [],
        dependency_tree=analysis.dependency_tree,
        critical_dependencies=analysis.critical_dependencies or [],
    )


@router.get("/changes/{change_id}/impact-report")
async def get_impact_report(
    change_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成影响报告"""
    analysis = db.query(ChangeImpactAnalysis).filter(
        ChangeImpactAnalysis.change_request_id == change_id
    ).order_by(ChangeImpactAnalysis.created_at.desc()).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="未找到影响分析结果")
    
    from datetime import datetime
    
    return {
        "change_request_id": change_id,
        "report_generated_at": datetime.now(),
        "summary": analysis.analysis_summary or "影响分析报告",
        "overall_risk_level": analysis.overall_risk_level or "MEDIUM",
        "overall_risk_score": float(analysis.overall_risk_score or 50),
        "schedule_impact": {
            "level": analysis.schedule_impact_level,
            "delay_days": analysis.schedule_delay_days,
            "affected_tasks_count": analysis.schedule_affected_tasks_count,
            "critical_path_affected": analysis.schedule_critical_path_affected,
            "description": analysis.schedule_impact_description,
        },
        "cost_impact": {
            "level": analysis.cost_impact_level,
            "amount": float(analysis.cost_impact_amount or 0),
            "percentage": float(analysis.cost_impact_percentage or 0),
            "description": analysis.cost_impact_description,
        },
        "quality_impact": {
            "level": analysis.quality_impact_level,
            "description": analysis.quality_impact_description,
        },
        "resource_impact": {
            "level": analysis.resource_impact_level,
            "description": analysis.resource_impact_description,
        },
        "chain_reactions": {
            "detected": analysis.chain_reaction_detected,
            "depth": analysis.chain_reaction_depth,
        },
        "recommendations": [analysis.recommended_action] if analysis.recommended_action else [],
        "action_items": [],
    }


# ============================================================
# 应对方案 API
# ============================================================

@router.post("/changes/{change_id}/suggestions", response_model=List[ChangeResponseSuggestionResponse])
async def generate_suggestions(
    change_id: int,
    request: SuggestionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成应对方案"""
    # 获取最新的影响分析
    analysis = db.query(ChangeImpactAnalysis).filter(
        ChangeImpactAnalysis.change_request_id == change_id
    ).order_by(ChangeImpactAnalysis.created_at.desc()).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="请先进行影响分析")
    
    try:
        service = ChangeResponseSuggestionService(db)
        suggestions = await service.generate_suggestions(
            change_id,
            analysis.id,
            current_user.id,
            request.max_suggestions
        )
        return suggestions
    except Exception as e:
        logger.error(f"生成应对方案失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/changes/{change_id}/suggestions", response_model=List[ChangeResponseSuggestionResponse])
async def list_suggestions(
    change_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取方案列表"""
    suggestions = db.query(ChangeResponseSuggestion).filter(
        ChangeResponseSuggestion.change_request_id == change_id
    ).order_by(
        ChangeResponseSuggestion.suggestion_priority.desc(),
        ChangeResponseSuggestion.created_at.desc()
    ).all()
    
    return suggestions


@router.get("/changes/{change_id}/suggestions/{suggestion_id}", response_model=ChangeResponseSuggestionResponse)
async def get_suggestion(
    change_id: int,
    suggestion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取方案详情"""
    suggestion = db.query(ChangeResponseSuggestion).filter(
        ChangeResponseSuggestion.id == suggestion_id,
        ChangeResponseSuggestion.change_request_id == change_id
    ).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    return suggestion


@router.put("/changes/{change_id}/suggestions/{suggestion_id}/select")
async def select_suggestion(
    change_id: int,
    suggestion_id: int,
    request: SuggestionSelectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """选择方案"""
    suggestion = db.query(ChangeResponseSuggestion).filter(
        ChangeResponseSuggestion.id == suggestion_id,
        ChangeResponseSuggestion.change_request_id == change_id
    ).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    from datetime import datetime
    
    suggestion.status = "SELECTED"
    suggestion.selected_at = datetime.now()
    suggestion.selected_by = current_user.id
    suggestion.selection_reason = request.selection_reason
    
    db.commit()
    
    return {"message": "方案已选择", "suggestion_id": suggestion_id}


# ============================================================
# 统计分析 API
# ============================================================

@router.get("/changes/impact-stats")
async def get_impact_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """影响统计"""
    from sqlalchemy import func
    
    # 总数统计
    total_changes = db.query(func.count(ChangeRequest.id)).scalar()
    total_analyses = db.query(func.count(ChangeImpactAnalysis.id)).scalar()
    
    # 按风险级别统计
    risk_stats = db.query(
        ChangeImpactAnalysis.overall_risk_level,
        func.count(ChangeImpactAnalysis.id)
    ).group_by(ChangeImpactAnalysis.overall_risk_level).all()
    
    by_risk_level = {level: count for level, count in risk_stats}
    
    # 平均值
    avg_duration = db.query(func.avg(ChangeImpactAnalysis.analysis_duration_ms)).scalar() or 0
    avg_risk_score = db.query(func.avg(ChangeImpactAnalysis.overall_risk_score)).scalar() or 0
    avg_confidence = db.query(func.avg(ChangeImpactAnalysis.ai_confidence_score)).scalar() or 0
    
    # 特殊情况统计
    chain_reaction_count = db.query(func.count(ChangeImpactAnalysis.id)).filter(
        ChangeImpactAnalysis.chain_reaction_detected == True
    ).scalar()
    
    critical_path_count = db.query(func.count(ChangeImpactAnalysis.id)).filter(
        ChangeImpactAnalysis.schedule_critical_path_affected == True
    ).scalar()
    
    budget_exceeded_count = db.query(func.count(ChangeImpactAnalysis.id)).filter(
        ChangeImpactAnalysis.cost_budget_exceeded == True
    ).scalar()
    
    return {
        "total_changes": total_changes,
        "total_analyses": total_analyses,
        "by_risk_level": by_risk_level,
        "by_impact_type": {},
        "by_recommended_action": {},
        "average_analysis_duration_ms": int(avg_duration),
        "average_risk_score": float(avg_risk_score),
        "average_confidence_score": float(avg_confidence),
        "chain_reaction_rate": float(chain_reaction_count / total_analyses * 100 if total_analyses > 0 else 0),
        "critical_path_impact_rate": float(critical_path_count / total_analyses * 100 if total_analyses > 0 else 0),
        "budget_exceeded_rate": float(budget_exceeded_count / total_analyses * 100 if total_analyses > 0 else 0),
    }


@router.get("/changes/effectiveness")
async def get_effectiveness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """方案有效性分析"""
    from sqlalchemy import func
    
    total = db.query(func.count(ChangeResponseSuggestion.id)).scalar()
    selected = db.query(func.count(ChangeResponseSuggestion.id)).filter(
        ChangeResponseSuggestion.status == "SELECTED"
    ).scalar()
    implemented = db.query(func.count(ChangeResponseSuggestion.id)).filter(
        ChangeResponseSuggestion.implementation_status == "COMPLETED"
    ).scalar()
    
    avg_feasibility = db.query(func.avg(ChangeResponseSuggestion.feasibility_score)).scalar() or 0
    avg_effectiveness = db.query(func.avg(ChangeResponseSuggestion.effectiveness_score)).scalar() or 0
    avg_ai_score = db.query(func.avg(ChangeResponseSuggestion.ai_recommendation_score)).scalar() or 0
    
    return {
        "total_suggestions": total,
        "selected_count": selected,
        "implemented_count": implemented,
        "completed_count": implemented,
        "average_feasibility_score": float(avg_feasibility),
        "average_effectiveness_score": float(avg_effectiveness),
        "average_ai_recommendation_score": float(avg_ai_score),
        "by_type": {},
        "success_rate": float(implemented / total * 100 if total > 0 else 0),
        "cost_accuracy": {},
        "duration_accuracy": {},
        "top_successful_patterns": [],
        "lessons_learned": [],
    }
